from __future__ import annotations

import asyncio
import typing
from inspect import iscoroutine

from maize.core.http.request import Request
from maize.core.items.items import Item
from maize.core.processor import Processor
from maize.core.scheduler import Scheduler
from maize.core.task_manager import TaskManager
from maize.exceptions.spider_exception import OutputException
from maize.utils.log_util import get_logger
from maize.utils.project_util import load_class
from maize.utils.spider_util import transform


if typing.TYPE_CHECKING:
    from maize.core.crawler import Crawler
    from maize.core.downloader.base_downloader import BaseDownloader
    from maize.core.settings.settings_manager import SettingsManager
    from maize.core.spider.spider import Spider
    from maize.core.spider.task_spider import TaskSpider


class Engine:
    def __init__(self, crawler: "Crawler"):
        self.logger = get_logger(crawler.settings, self.__class__.__name__)
        self.crawler: "Crawler" = crawler
        self.settings: "SettingsManager" = self.crawler.settings

        self.downloader: typing.Optional["BaseDownloader"] = None
        self.scheduler: typing.Optional[Scheduler] = None
        self.processor: typing.Optional[Processor] = None

        self.start_requests: typing.Optional[typing.AsyncGenerator] = None
        self.task_requests: typing.Optional[typing.AsyncIterator[Request]] = None

        self.spider: typing.Optional[typing.Union["Spider", "TaskSpider"]] = None
        self.task_manager: TaskManager = TaskManager(
            self.settings.getint("CONCURRENCY")
        )
        self.start_requests_running = False
        self.task_requests_running = False
        self._single_task_requests_running = False
        self.running = False

    def _get_downloader(self):
        downloader_cls = load_class(self.settings.get("DOWNLOADER"))
        if not issubclass(downloader_cls, BaseDownloader):
            raise TypeError(
                f"The downloader class ({self.settings.get('DOWNLOADER')}) "
                f"does not fully implement required interface"
            )
        return downloader_cls

    async def start_spider(self, spider: "Spider"):
        self.running = True
        self.start_requests_running = True

        self.logger.info(
            f"spider started. (project name: {self.settings.get('PROJECT_NAME')})"
        )
        self.spider = spider
        self.scheduler = Scheduler()
        if getattr(self.scheduler, "open"):
            self.scheduler.open()

        downloader_cls = load_class(self.settings.get("DOWNLOADER"))
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
                spider_task_requests: typing.AsyncGenerator[
                    Request, typing.Any
                ] = self.spider.task_requests()
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
            ):
                await self.processor.close()
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
            else:
                try:
                    start_request = await anext(self.start_requests)
                except StopAsyncIteration:
                    self.start_requests = None
                except Exception as e:
                    # 1. 发起请求的 task 全部运行完毕
                    # 2. 调度器是否空闲
                    # 3. 下载器是否空闲
                    if not await self._exit():
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
            else:
                try:
                    self.task_requests: typing.AsyncIterator[Request]
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
                    if not await self._exit():
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

    async def _fetch(
        self, request: Request
    ) -> typing.Optional[typing.AsyncGenerator[Request | Item, typing.Any]]:
        async def _success(_response):
            callback: typing.Callable = request.callback or self.spider.parse
            if _output := callback(_response):
                if iscoroutine(_output):
                    await _output
                else:
                    return transform(_output)

        download_result = await self.downloader.download(request)
        if download_result is None:
            return None

        if isinstance(download_result, Request):
            await self.enqueue_request(download_result)
            return None

        return await _success(download_result)

    async def enqueue_request(self, request: Request):
        # TODO: 去重
        await self._schedule_request(request)

    async def _schedule_request(self, request: Request):
        await self.scheduler.enqueue_request(request)

    async def _get_next_request(self):
        return await self.scheduler.next_request()

    async def _handle_spider_output(
        self, outputs: typing.AsyncGenerator[Request | Item, typing.Any]
    ):
        async for spider_output in outputs:
            if isinstance(spider_output, (Request, Item)):
                await self.processor.enqueue(spider_output)
            else:
                raise OutputException(
                    f"{type(spider_output)} must return `Request` or `Item`"
                )

    async def _exit(self) -> bool:
        if (
            self.scheduler.idle()
            and self.downloader.idle()
            and self.task_manager.all_done()
            and self.processor.idle()
        ):
            return True
        return False

    async def close_spider(self):
        self.logger.info("Closing spider")
        await self.downloader.close()
