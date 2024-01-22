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


class Engine:
    def __init__(self, crawler: "Crawler"):
        self.logger = get_logger(name=self.__class__.__name__, crawler=crawler)
        self.crawler: "Crawler" = crawler
        self.settings: "SettingsManager" = self.crawler.settings

        self.downloader: typing.Optional["BaseDownloader"] = None
        self.scheduler: typing.Optional[Scheduler] = None
        self.processor: typing.Optional[Processor] = None

        self.start_requests: typing.Optional[typing.Generator] = None
        self.spider: typing.Optional["Spider"] = None
        self.task_manager: TaskManager = TaskManager(
            self.settings.getint("CONCURRENCY")
        )
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
            self.downloader.open()

        self.processor = Processor(self.crawler)
        self.start_requests = iter(spider.start_requests())
        await self._open_spider()

    async def _open_spider(self):
        crawling = asyncio.create_task(self.crawl())
        await crawling

    async def crawl(self):
        """主逻辑"""
        while self.running:
            if request := await self._get_next_request():
                await self._crawl(request)
            else:
                try:
                    start_request = next(self.start_requests)
                except StopIteration:
                    self.start_requests = None
                except Exception as e:
                    # 1. 发起请求的 task 全部运行完毕
                    # 2. 调度器是否空闲
                    # 3. 下载器是否空闲
                    if not await self._exit():
                        continue
                    self.running = False

                    if self.start_requests is not None:
                        self.logger.info(f"Error during start_requests: {e}")
                else:
                    await self.enqueue_request(start_request)

        if not self.running:
            await self.close_spider()

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
