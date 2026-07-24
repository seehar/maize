"""同步爬虫引擎。

与异步版 ``AioEngine`` 对应，使用线程池替代 asyncio 实现并发。
调度逻辑、中间件链、下载-解析-入队流程与异步版一致，全部为同步调用。

关键差异：
- ``asyncio.create_task`` → ``SyncTaskManager.create_task``（线程池 Future）
- ``await callback(response)`` → ``callback(response)``（直接同步调用）
- ``asyncio.sleep`` → ``time.sleep``
- ``anext(gen)`` → ``next(gen)``
- 不支持 Redis 分布式（同步 Redis 需额外依赖，暂不引入）
"""

from __future__ import annotations

import time
from collections.abc import Generator
from typing import TYPE_CHECKING, Any, Union

from maize.common.http import Request, Response
from maize.common.items import Item
from maize.common.model.download_response_model import DownloadResponse
from maize.exceptions.spider_exception import (
    OutputException,
    StartRequestsNotImplementedException,
)
from maize.sync.classic.downloader.sync_base_downloader import SyncBaseDownloader
from maize.sync.classic.middleware.sync_middleware_manager import (
    SyncDownloaderMiddlewareManager,
    SyncSpiderMiddlewareManager,
)
from maize.sync.classic.processor.sync_processor import SyncProcessor
from maize.sync.classic.scheduler import SyncSpiderPriorityQueue
from maize.sync.classic.task.sync_task_manager import SyncTaskManager
from maize.utils.log_util import get_logger
from maize.utils.project_util import load_class
from maize.utils.spider_util import transform_sync

if TYPE_CHECKING:
    from maize.settings import SpiderSettings
    from maize.sync.classic.crawler.sync_crawler import SyncCrawler
    from maize.sync.classic.spider.sync_spider import SyncSpider


class SyncEngine:
    """同步爬虫引擎。"""

    def __init__(self, crawler: SyncCrawler):
        """
        初始化同步引擎。

        :param crawler: 当前 SyncCrawler 实例
        """
        self.logger = get_logger(crawler.settings, self.__class__.__name__)
        self.crawler: SyncCrawler = crawler
        self.settings: SpiderSettings = self.crawler.settings

        self.downloader: SyncBaseDownloader | None = None
        self.scheduler: SyncSpiderPriorityQueue | None = None
        self.processor: SyncProcessor | None = None

        self.start_requests: Generator | None = None
        self.task_requests: Generator[Request, Any, None] | None = None

        self.spider: SyncSpider | None = None
        self.task_manager = SyncTaskManager(self.settings.concurrency, logger=self.logger)
        self.start_requests_running = False
        self.task_requests_running = False
        self._single_task_requests_running = False
        self.running = False

        # 中间件管理器
        self.downloader_middleware_manager: SyncDownloaderMiddlewareManager | None = None
        self.spider_middleware_manager: SyncSpiderMiddlewareManager | None = None

    def _get_downloader(self):
        """获取下载器类，校验是否实现了 SyncBaseDownloader 接口。"""
        downloader_cls = load_class(self.settings.downloader)
        if not issubclass(downloader_cls, SyncBaseDownloader):
            raise TypeError(
                f"The downloader class ({self.settings.downloader}) does not fully implement required interface"
            )
        return downloader_cls

    def _create_scheduler(self) -> SyncSpiderPriorityQueue:
        """创建同步调度器。测试可重写注入 mock。"""
        return SyncSpiderPriorityQueue()

    def _create_downloader(self) -> SyncBaseDownloader:
        """创建并打开同步下载器。测试可重写注入 mock。"""
        downloader_cls = load_class(self.settings.downloader)
        downloader = downloader_cls(self.crawler)
        downloader.open()
        return downloader

    def start_spider(self, spider: SyncSpider):
        """
        启动 Spider，初始化调度器、中间件、下载器、处理器和任务管理器。

        :param spider: 要运行的 SyncSpider 实例
        :raises StartRequestsNotImplementedException: start_requests 未实现或不是生成器
        """
        self.running = True
        self.start_requests_running = True

        self.logger.info(f"spider started. (project name: {self.settings.project_name})")
        self.spider = spider
        self.scheduler = self._create_scheduler()

        # 初始化中间件管理器
        self.downloader_middleware_manager = SyncDownloaderMiddlewareManager(
            self.crawler, self.settings.middleware.downloader_middlewares
        )
        self.downloader_middleware_manager.open()

        self.spider_middleware_manager = SyncSpiderMiddlewareManager(
            self.crawler, self.settings.middleware.spider_middlewares
        )
        self.spider_middleware_manager.open()

        self.downloader = self._create_downloader()

        self.processor = SyncProcessor(self.crawler)
        self.processor.open()

        self.task_manager.open()

        # 校验 start_requests 是否已实现
        try:
            start_requests_result = spider.start_requests()
            # 检查是否是一个生成器
            if not hasattr(start_requests_result, "__next__"):
                raise StartRequestsNotImplementedException(
                    f"Spider {spider.__class__.__name__}.start_requests() must be implemented as a generator"
                )
            self.start_requests = start_requests_result
        except NotImplementedError:
            raise StartRequestsNotImplementedException(
                f"Spider {spider.__class__.__name__}.start_requests() must be implemented"
            ) from None

        self._open_spider()

    def _open_spider(self):
        self.crawl()

    def crawl(self):
        """主逻辑"""
        while self.running:
            self._crawl_start_requests()

            # 任务爬虫
            if self.spider and self.spider.__spider_type__ == "task_spider":
                self.logger.info("Task spider start get task requests")
                spider_task_requests: Generator[Request, Any, None] = self.spider.start_requests()
                if spider_task_requests:
                    self.task_requests = spider_task_requests
                    self.task_requests_running = True
                    self._single_task_requests_running = True
                    self._crawl_task_requests()
                else:
                    self.task_requests_running = False

            if (
                self.start_requests_running is False
                and self.task_requests_running is False
                and self.task_manager.all_done()
            ):
                self.running = False

        if not self.running:
            self.close_spider()

    def _crawl_start_requests(self):
        """普通爬虫的 start_requests 处理逻辑"""
        start_requests: Generator | None = None
        if self.spider_middleware_manager and self.start_requests:
            start_requests = self.spider_middleware_manager.process_start_requests(
                self.start_requests,
                self.spider,  # type: ignore[arg-type]
            )
        else:
            start_requests = self.start_requests

        while self.start_requests_running:
            if request := self._get_next_request():
                self._crawl(request)
                continue

            try:
                assert start_requests is not None
                start_request: Request = next(start_requests)
            except StopIteration:
                self.start_requests = None
                if not self._idle():
                    time.sleep(0.1)
                    continue

                self.start_requests_running = False
                self.logger.info("All start requests have been processed.")
            except Exception as e:
                if not self._idle():
                    time.sleep(0.1)
                    continue

                self.start_requests_running = False
                self.logger.info("All start requests have been processed.")

                if self.start_requests is not None:
                    self.logger.info(f"Error during start_requests: {e}")
            else:
                self.enqueue_request(start_request)

    def _crawl_task_requests(self):
        """任务爬虫 task_requests 处理逻辑"""
        while self._single_task_requests_running:
            if request := self._get_next_request():
                self._crawl(request)
                continue

            try:
                assert self.task_requests is not None
                task_request = next(self.task_requests)
            except StopIteration:
                self.task_requests = None
                self._single_task_requests_running = False
                self.task_requests_running = False
                self.logger.info("All task requests have been processed.")
            except Exception as e:
                had_task_requests = self.task_requests is not None
                self.task_requests = None
                if not self._idle():
                    time.sleep(0.1)
                    continue

                self._single_task_requests_running = False
                self.logger.info("All task requests have been processed.")

                if had_task_requests:
                    self.logger.info(f"Error during task_requests: {e}")
            else:
                self.enqueue_request(task_request)

    def _crawl(self, request: Request):
        def crawl_task():
            outputs = self._fetch(request)
            if outputs:
                self._handle_spider_output(outputs)

        self.task_manager.semaphore.acquire()
        self.task_manager.create_task(crawl_task)

    def _fetch(self, request: Request) -> Generator[Union[Request, Item], Any, None] | None:
        """
        执行单个请求的完整抓取流程：中间件 → 下载 → 响应处理 → 回调解析。

        :param request: 待抓取的请求
        :return: Spider 产出的生成器，无产出返回 None
        """
        # Apply downloader middleware process_request
        request_or_response = self._process_request_middleware(request)
        if request_or_response is None:
            return None
        if isinstance(request_or_response, Response):
            return self._handle_success_response(request_or_response, request)
        request = request_or_response

        # Download and process result
        download_result = self._do_download(request)
        if download_result is None or isinstance(download_result, Request):
            if isinstance(download_result, Request):
                self.enqueue_request(download_result)
            return None

        if download_result.response is None:
            if self.spider and self.spider.stats_collector:
                self.spider.stats_collector.record_download_fail(download_result.reason)
            return self._handle_error_response(request)

        # Apply downloader middleware process_response
        response = self._process_response_middleware(request, download_result.response)
        if response is None:
            return None

        if self.spider and self.spider.stats_collector:
            self.spider.stats_collector.record_download_success(response.status)
        return self._handle_success_response(response, request)

    def _process_request_middleware(self, request: Request) -> Union[Request, Response] | None:
        """处理请求中间件"""
        if not self.downloader_middleware_manager:
            return request
        assert self.spider is not None
        result = self.downloader_middleware_manager.process_request(request, self.spider)
        if result is None:
            return None
        if isinstance(result, Response):
            return result
        return result

    def _do_download(self, request: Request):
        """执行下载"""
        try:
            assert self.downloader is not None
            return self.downloader.fetch(request)
        except Exception as e:
            if not self.downloader_middleware_manager:
                raise
            assert self.spider is not None
            result = self.downloader_middleware_manager.process_exception(request, e, self.spider)
            if result is None:
                raise
            if isinstance(result, Request):
                self.enqueue_request(result)
                return None
            if isinstance(result, Response):
                return DownloadResponse(response=result)
            return None

    def _process_response_middleware(self, request: Request, response: Response) -> Response | None:
        """处理响应中间件"""
        if not self.downloader_middleware_manager:
            return response
        assert self.spider is not None
        result = self.downloader_middleware_manager.process_response(request, response, self.spider)
        if result is None:
            return None
        if isinstance(result, Request):
            self.enqueue_request(result)
            return None
        return result

    def _handle_success_response(
        self, response: Response, request: Request
    ) -> Generator[Union[Request, Item], Any, None] | None:
        """处理成功的响应"""
        if self.spider_middleware_manager:
            try:
                assert self.spider is not None
                should_continue = self.spider_middleware_manager.process_spider_input(response, self.spider)
                if not should_continue:
                    return None
            except Exception as e:
                self.logger.error(f"Error in spider middleware process_spider_input: {e}")
                return None

        assert self.spider is not None
        callback = request.callback or self.spider.parse
        try:
            _output = callback(response)
            if _output:
                # 直接交给 transform_sync 判断是否为 generator，避免 list 等 __iter__ 误入
                transform_output = transform_sync(_output)

                if self.spider_middleware_manager:
                    transform_output = self.spider_middleware_manager.process_spider_output(
                        response, transform_output, self.spider
                    )

                if self.spider.stats_collector:
                    self.spider.stats_collector.record_parse_success()
                return transform_output
        except Exception as e:
            self.logger.error(f"Error during callback: {e}")
            if self.spider.stats_collector:
                self.spider.stats_collector.record_parse_fail()

        return None

    def _handle_error_response(self, request: Request) -> Generator[Union[Request, Item], Any, None] | None:
        """处理错误的响应"""
        error_callback = request.error_callback
        if not error_callback:
            return None

        try:
            _error_output = error_callback(request)
            if _error_output:
                transform_output = transform_sync(_error_output)
                assert self.spider is not None
                if self.spider.stats_collector:
                    self.spider.stats_collector.record_parse_fail()
                return transform_output
        except Exception as e:
            self.logger.error(f"Error during error_callback: {e}")
        return None

    def enqueue_request(self, request: Request):
        """
        将请求入队到调度器。

        :param request: 待入队的请求
        """
        assert self.scheduler is not None
        self.scheduler.put(request)

    def _get_next_request(self) -> Request | None:
        """
        从调度器获取下一个请求。

        :return: 下一个请求，无可用请求返回 None
        """
        assert self.scheduler is not None
        assert self.crawler.spider is not None
        gte = self.crawler.spider.gte_priority
        return self.scheduler.get_by_priority(gte) if gte is not None else self.scheduler.get()

    def _handle_spider_output(self, outputs: Generator[Union[Request, Item], Any, None]):
        assert self.processor is not None
        for spider_output in outputs:
            if isinstance(spider_output, Request | Item):
                self.processor.enqueue(spider_output)
            else:
                raise OutputException(f"{type(spider_output)} must return `Request` or `Item`")

    def _scheduler_idle(self) -> bool:
        """调度器是否空闲。测试可重写。"""
        assert self.scheduler is not None
        return self.scheduler.qsize() == 0

    def _idle(self) -> bool:
        return (
            self.scheduler is not None
            and self._scheduler_idle()
            and self.downloader is not None
            and self.downloader.idle()
            and self.task_manager.all_done()
            and self.processor is not None
            and self.processor.idle()
            and self.crawler.idle()
        )

    def close_spider(self):
        """
        关闭 Spider，等待线程任务完成后依次关闭中间件、下载器、处理器和任务管理器。
        """
        self.logger.info("Closing spider")
        # 等待所有线程任务完成
        while not self.task_manager.all_done():
            time.sleep(0.1)

        if self.downloader_middleware_manager:
            self.downloader_middleware_manager.close()
        if self.spider_middleware_manager:
            self.spider_middleware_manager.close()
        assert self.downloader is not None
        self.downloader.close()
        assert self.processor is not None
        self.processor.close()
        self.task_manager.close()
