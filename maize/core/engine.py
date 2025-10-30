from __future__ import annotations

import asyncio
from inspect import iscoroutine
from typing import TYPE_CHECKING
from typing import Any
from typing import AsyncGenerator
from typing import AsyncIterator
from typing import Callable
from typing import Optional
from typing import Union

import ujson

from maize import Response
from maize.common.http.request import Request
from maize.common.items import Item
from maize.core.processor import Processor
from maize.core.scheduler import Scheduler
from maize.core.task_manager import TaskManager
from maize.exceptions.spider_exception import OutputException


try:
    from maize.utils.redis_util import RedisUtil
except ImportError:
    RedisUtil = None
from maize.utils.log_util import get_logger
from maize.utils.project_util import load_class
from maize.utils.spider_util import transform
from maize.utils.string_util import StringUtil


if TYPE_CHECKING:
    from maize.core.crawler import Crawler
    from maize.downloader.base.base_downloader import BaseDownloader
    from maize.settings import SpiderSettings
    from maize.spider.spider import Spider
    from maize.spider.task_spider import TaskSpider


class Engine:
    """
    爬虫引擎
    """

    def __init__(self, crawler: "Crawler"):
        self.logger = get_logger(crawler.settings, self.__class__.__name__)
        self.crawler: "Crawler" = crawler
        self.settings: "SpiderSettings" = self.crawler.settings

        self.downloader: Optional["BaseDownloader"] = None
        self.scheduler: Optional[Scheduler] = None
        self.processor: Optional[Processor] = None

        self.start_requests: Optional[AsyncGenerator] = None
        self.task_requests: Optional[AsyncIterator[Request]] = None

        self.spider: Optional[Union["Spider", "TaskSpider"]] = None
        self.task_manager: TaskManager = TaskManager(self.settings.CONCURRENCY)
        self.start_requests_running = False
        self.task_requests_running = False
        self._single_task_requests_running = False
        self.running = False

        # 分布式
        self.is_distributed = self.settings.IS_DISTRIBUTED
        self.__redis_util = None
        self.__redis_key_distributed_lock = None
        self.__redis_key_queue = None
        self.__redis_key_running = None

    def __init_redis(self):
        if self.is_distributed or self.settings.USE_REDIS:
            self.__redis_util = RedisUtil(self.settings.redis_url)
            self.__redis_key_distributed_lock = self.__get_redis_key(self.settings.REDIS_KEY_LOCK)
            self.__redis_key_queue = self.__get_redis_key(self.settings.REDIS_KEY_QUEUE)
            self.__redis_key_running = self.__get_redis_key(self.settings.REDIS_KEY_RUNNING)

    def __get_redis_key(self, key: str) -> str:
        redis_key_prefix = self.settings.REDIS_KEY_PREFIX
        spider_name = StringUtil.camel_to_snake(self.spider.__class__.__name__)
        return f"{redis_key_prefix}:{spider_name}:{key}"

    def _get_downloader(self):
        downloader_cls = load_class(self.settings.DOWNLOADER)
        if not issubclass(downloader_cls, BaseDownloader):
            raise TypeError(
                f"The downloader class ({self.settings.DOWNLOADER}) " f"does not fully implement required interface"
            )
        return downloader_cls

    async def start_spider(self, spider: "Spider"):
        self.running = True
        self.start_requests_running = True

        self.logger.info(f"spider started. (project name: {self.settings.PROJECT_NAME})")
        self.spider = spider
        self.__init_redis()
        self.scheduler = Scheduler()
        if getattr(self.scheduler, "open"):
            self.scheduler.open()

        downloader_cls = load_class(self.settings.DOWNLOADER)
        self.downloader = downloader_cls(self.crawler)
        if getattr(self.downloader, "open"):
            await self.downloader.open()

        self.processor = Processor(self.crawler)
        await self.processor.open()
        self.start_requests = aiter(spider.start_requests())
        await self._open_spider()

    async def _open_spider(self):
        crawling = asyncio.create_task(self.crawl())
        await crawling

    async def crawl(self):
        """主逻辑"""
        while self.running:
            await self._crawl_start_requests()

            # 任务爬虫
            if self.spider.__spider_type__ == "task_spider":
                self.logger.info("Task spider start get task requests")
                spider_task_requests: AsyncGenerator[Request, Any] = self.spider.task_requests()
                if spider_task_requests:
                    self.task_requests = aiter(spider_task_requests)
                    self.task_requests_running = True
                    self._single_task_requests_running = True
                    await self._crawl_task_requests()
                else:
                    self.task_requests_running = False

            if (
                self.start_requests_running is False
                and self.task_requests_running is False
                and self.task_manager.all_done()
            ):
                self.running = False

        if not self.running:
            await self.close_spider()

    async def _crawl_start_requests(self):
        """
        普通爬虫的 start_requests 处理逻辑
        :return:
        """
        while self.start_requests_running:
            if request := await self._get_next_request():
                await self._crawl(request)
                continue

            try:
                start_request: Request = await anext(self.start_requests)
            except StopAsyncIteration:
                self.start_requests = None
            except Exception as e:
                # 1. 发起请求的 task 全部运行完毕
                # 2. 调度器是否空闲
                # 3. 下载器是否空闲
                if not self._idle():
                    await asyncio.sleep(0.1)
                    continue

                self.start_requests_running = False
                self.logger.info("All start requests have been processed.")

                if self.start_requests is not None:
                    self.logger.info(f"Error during start_requests: {e}")
            else:
                await self.enqueue_request(start_request)

    async def _crawl_task_requests(self):
        """
        任务爬虫 task_requests 处理逻辑
        :return:
        """
        while self._single_task_requests_running:
            if request := await self._get_next_request():
                await self._crawl(request)
                continue

            try:
                self.task_requests: AsyncIterator[Request]
                task_request = await anext(self.task_requests)
            except StopAsyncIteration:
                self.task_requests = None
            except RuntimeError:
                self.task_requests_running = False
            except Exception as e:
                # 1. 发起请求的 task 全部运行完毕
                # 2. 调度器是否空闲
                # 3. 下载器是否空闲
                self.task_requests = None
                if not self._idle():
                    await asyncio.sleep(0.1)
                    continue

                self._single_task_requests_running = False
                self.logger.info("All task requests have been processed.")

                if self.task_requests is not None:
                    self.logger.info(f"Error during start_requests: {e}")
            else:
                await self.enqueue_request(task_request)

    async def _crawl(self, request: Request):
        async def crawl_task():
            outputs = await self._fetch(request)
            if outputs:
                await self._handle_spider_output(outputs)

        await self.task_manager.semaphore.acquire()
        self.task_manager.create_task(crawl_task())

    async def _fetch(self, request: Request) -> Optional[AsyncGenerator[Union[Request, Item], Any]]:
        async def _success(_response: Response) -> Optional[AsyncGenerator[Union[Request, Item], Any]]:
            callback: Callable = request.callback or self.spider.parse
            if _output := callback(_response):
                try:
                    if iscoroutine(_output):
                        await _output
                        await self.spider.stats_collector.record_parse_success()
                    else:
                        transform_output = transform(_output)
                        await self.spider.stats_collector.record_parse_success()
                        return transform_output
                except Exception as e:
                    self.logger.error(f"Error during callback: {e}")
                    await self.spider.stats_collector.record_parse_fail()

            if self.__redis_util:
                self.logger.debug(f"redis delete {self.__redis_key_running}:{request.hash}")
                await self.__redis_util.delete(f"{self.__redis_key_running}:{request.hash}")
            return None

        async def _error(_request: Request) -> Optional[AsyncGenerator[Union[Request, Item], Any]]:
            error_callback: Callable = request.error_callback
            if not error_callback:
                return None

            if _error_output := error_callback(_request):
                try:
                    if iscoroutine(_error_output):
                        await _error_output
                        await self.spider.stats_collector.record_parse_fail()
                    else:
                        transform_output = transform(_error_output)
                        await self.spider.stats_collector.record_parse_fail()
                        return transform_output
                except Exception as e:
                    self.logger.error(f"Error during error_callback: {e}")

            if self.__redis_util:
                self.logger.debug(f"redis delete {self.__redis_key_running}:{request.hash}")
                await self.__redis_util.delete(f"{self.__redis_key_running}:{request.hash}")
            return None

        download_result = await self.downloader.fetch(request)
        if isinstance(download_result, Request):
            await self.enqueue_request(download_result)
            return None

        if download_result is None or download_result.response is None:
            # 下载失败
            await self.spider.stats_collector.record_download_fail(download_result.reason)
            return await _error(request)

        # 下载成功
        await self.spider.stats_collector.record_download_success(download_result.response.status)
        return await _success(download_result.response)

    async def enqueue_request(self, request: Request):
        if self.__redis_util:
            await self.__redis_util.set(
                f"{self.__redis_key_queue}:{request.hash}",
                ujson.dumps(request.model_dump),
            )
        await self._schedule_request(request)

    async def _schedule_request(self, request: Request):
        await self.scheduler.enqueue_request(request)

    async def _get_next_request(self) -> Optional[Request]:
        request: Optional[Request] = await self.scheduler.next_request(self.crawler.spider.gte_priority)
        if not request:
            return None

        if self.is_distributed:
            nx_set_result = await self.__redis_util.nx_set(self.__redis_key_distributed_lock, request.hash, 600)
            if not nx_set_result:
                return None

        if self.__redis_util:
            await self.__redis_util.set(
                f"{self.__redis_key_running}:{request.hash}",
                ujson.dumps(request.model_dump),
            )
            self.logger.debug(f"redis delete {self.__redis_key_queue}:{request.hash}")
            await self.__redis_util.delete(f"{self.__redis_key_queue}:{request.hash}")
        return request

    async def _handle_spider_output(self, outputs: AsyncGenerator[Union[Request, Item], Any]):
        async for spider_output in outputs:
            if isinstance(spider_output, (Request, Item)):
                await self.processor.enqueue(spider_output)
            else:
                raise OutputException(f"{type(spider_output)} must return `Request` or `Item`")

    def _idle(self) -> bool:
        return (
            self.scheduler.idle()
            and self.downloader.idle()
            and self.task_manager.all_done()
            and self.processor.idle()
            and self.crawler.idle()
        )

    async def close_spider(self):
        self.logger.info("Closing spider")
        await self.downloader.close()
        await self.processor.close()
