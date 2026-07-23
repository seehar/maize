"""同步中间件管理器。

与异步版 ``MiddlewareManager`` 对应，所有 ``process_*`` 方法为同步。
加载、排序、生命周期管理与异步版一致。
"""

from collections.abc import Generator
from typing import TYPE_CHECKING

from maize.sync.classic.middleware.sync_base_middleware import (
    SyncBaseMiddleware,
    SyncDownloaderMiddleware,
    SyncPipelineMiddleware,
    SyncSpiderMiddleware,
)
from maize.utils.log_util import get_logger
from maize.utils.project_util import load_class

if TYPE_CHECKING:
    from maize.common.http.request import Request
    from maize.common.http.response import Response
    from maize.common.items import Item
    from maize.sync.classic.crawler.sync_crawler import SyncCrawler
    from maize.sync.classic.spider.sync_spider import SyncSpider


class SyncMiddlewareManager:
    """同步中间件管理器基类。"""

    def __init__(self, crawler: "SyncCrawler", middleware_configs: dict[str | type, int]):
        self.crawler = crawler
        self.settings = crawler.settings
        self.middleware_configs = middleware_configs
        self.logger = get_logger(self.settings, self.__class__.__name__)
        self.middlewares: list[tuple[SyncBaseMiddleware, int]] = []

    def _load_middleware(self, middleware_path_or_cls: str | type, priority: int) -> SyncBaseMiddleware | None:
        try:
            middleware_cls = load_class(middleware_path_or_cls)
            if hasattr(middleware_cls, "from_crawler"):
                middleware = middleware_cls.from_crawler(self.crawler)
            else:
                middleware = middleware_cls(self.settings)
            middleware_name = (
                middleware_cls.__name__ if hasattr(middleware_cls, "__name__") else str(middleware_path_or_cls)
            )
            self.logger.debug(f"Loaded middleware: {middleware_name} (priority: {priority})")
            return middleware  # type: ignore[no-any-return]
        except Exception as e:
            self.logger.error(f"Failed to load middleware {middleware_path_or_cls}: {e}")
            return None

    def open(self):
        for middleware_path, priority in self.middleware_configs.items():
            middleware = self._load_middleware(middleware_path, priority)
            if middleware:
                self.middlewares.append((middleware, priority))

        self.middlewares.sort(key=lambda x: x[1])

        for middleware, _ in self.middlewares:
            try:
                middleware.open()
            except Exception as e:
                self.logger.error(f"Error opening middleware {middleware.__class__.__name__}: {e}")

    def close(self):
        for middleware, _ in self.middlewares:
            try:
                middleware.close()
            except Exception as e:
                self.logger.error(f"Error closing middleware {middleware.__class__.__name__}: {e}")


class SyncDownloaderMiddlewareManager(SyncMiddlewareManager):
    """同步下载器中间件管理器。"""

    def process_request(self, request: "Request", spider: "SyncSpider") -> "Request | Response | None":
        for middleware, _ in self.middlewares:
            if not isinstance(middleware, SyncDownloaderMiddleware):
                continue
            try:
                result = middleware.process_request(request, spider)
                if isinstance(result, Response):
                    self.logger.debug(
                        f"Middleware {middleware.__class__.__name__} returned Response, stopping request processing"
                    )
                    return result
                if result is None:
                    self.logger.debug(f"Middleware {middleware.__class__.__name__} dropped request: {request.url}")
                    return None
                request = result
            except Exception as e:
                self.logger.error(f"Error in {middleware.__class__.__name__}.process_request for {request.url}: {e}")
                continue
        return request

    def process_response(
        self, request: "Request", response: "Response", spider: "SyncSpider"
    ) -> "Response | Request | None":
        for middleware, _ in reversed(self.middlewares):
            if not isinstance(middleware, SyncDownloaderMiddleware):
                continue
            try:
                result = middleware.process_response(request, response, spider)
                if isinstance(result, Request):
                    self.logger.debug(f"Middleware {middleware.__class__.__name__} returned Request, will retry")
                    return result
                if result is None:
                    self.logger.debug(f"Middleware {middleware.__class__.__name__} dropped response for {request.url}")
                    return None
                response = result
            except Exception as e:
                self.logger.error(f"Error in {middleware.__class__.__name__}.process_response for {request.url}: {e}")
                continue
        return response

    def process_exception(
        self, request: "Request", exception: Exception, spider: "SyncSpider"
    ) -> "Request | Response | None":
        for middleware, _ in reversed(self.middlewares):
            if not isinstance(middleware, SyncDownloaderMiddleware):
                continue
            try:
                result = middleware.process_exception(request, exception, spider)
                if result is not None:
                    self.logger.debug(f"Middleware {middleware.__class__.__name__} handled exception for {request.url}")
                    return result
            except Exception as e:
                self.logger.error(f"Error in {middleware.__class__.__name__}.process_exception for {request.url}: {e}")
                continue
        return None


class SyncSpiderMiddlewareManager(SyncMiddlewareManager):
    """同步爬虫中间件管理器。"""

    def process_spider_input(self, response: "Response", spider: "SyncSpider") -> bool:
        for middleware, _ in self.middlewares:
            if not isinstance(middleware, SyncSpiderMiddleware):
                continue
            try:
                should_continue = middleware.process_spider_input(response, spider)
                if not should_continue:
                    return False
            except Exception as e:
                self.logger.error(f"Error in {middleware.__class__.__name__}.process_spider_input: {e}")
                result = self.process_spider_exception(response, e, spider)
                if result is not None:
                    return False
                raise
        return True

    def process_spider_output(self, response: "Response", result: Generator, spider: "SyncSpider") -> Generator:
        for middleware, _ in reversed(self.middlewares):
            if not isinstance(middleware, SyncSpiderMiddleware):
                continue
            try:
                result = middleware.process_spider_output(response, result, spider)
            except Exception as e:
                self.logger.error(f"Error in {middleware.__class__.__name__}.process_spider_output: {e}")
                continue
        yield from result

    def process_spider_exception(
        self, response: "Response", exception: Exception, spider: "SyncSpider"
    ) -> Generator | None:
        for middleware, _ in reversed(self.middlewares):
            if not isinstance(middleware, SyncSpiderMiddleware):
                continue
            try:
                result = middleware.process_spider_exception(response, exception, spider)
                if result is not None:
                    self.logger.debug(f"Middleware {middleware.__class__.__name__} handled spider exception")
                    return result
            except Exception as e:
                self.logger.error(f"Error in {middleware.__class__.__name__}.process_spider_exception: {e}")
                continue
        return None

    def process_start_requests(self, start_requests: Generator, spider: "SyncSpider") -> Generator:
        for middleware, _ in reversed(self.middlewares):
            if not isinstance(middleware, SyncSpiderMiddleware):
                continue
            try:
                start_requests = middleware.process_start_requests(start_requests, spider)
            except Exception as e:
                self.logger.error(f"Error in {middleware.__class__.__name__}.process_start_requests: {e}")
                continue
        yield from start_requests


class SyncPipelineMiddlewareManager(SyncMiddlewareManager):
    """同步管道中间件管理器。"""

    def process_item_before(self, item: "Item | None", spider: "SyncSpider") -> "Item | None":
        for middleware, _ in self.middlewares:
            if not isinstance(middleware, SyncPipelineMiddleware):
                continue
            try:
                item = middleware.process_item_before(item, spider)
                if item is None:
                    self.logger.debug(f"Middleware {middleware.__class__.__name__} dropped item")
                    return None
            except Exception as e:
                self.logger.error(f"Error in {middleware.__class__.__name__}.process_item_before: {e}")
                continue
        return item

    def process_item_after(self, item: "Item | None", spider: "SyncSpider") -> "Item | None":
        for middleware, _ in reversed(self.middlewares):
            if not isinstance(middleware, SyncPipelineMiddleware):
                continue
            try:
                item = middleware.process_item_after(item, spider)
                if item is None:
                    self.logger.debug(f"Middleware {middleware.__class__.__name__} dropped item")
                    return None
            except Exception as e:
                self.logger.error(f"Error in {middleware.__class__.__name__}.process_item_after: {e}")
                continue
        return item
