"""
Maize 框架的中间件管理器

本模块提供管理器，用于根据优先级加载、实例化和执行中间件
"""

from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

from maize.middlewares.base_middleware import (
    BaseMiddleware,
    DownloaderMiddleware,
    PipelineMiddleware,
    SpiderMiddleware,
)
from maize.utils.log_util import get_logger
from maize.utils.project_util import load_class

if TYPE_CHECKING:
    from maize.common.http.request import Request
    from maize.common.http.response import Response
    from maize.common.items import Item
    from maize.core.crawler import Crawler
    from maize.spider.spider import Spider


class MiddlewareManager:
    """
    所有中间件类型的基础管理器类

    处理中间件的加载、实例化和生命周期管理
    """

    def __init__(self, crawler: "Crawler", middleware_configs: dict[str | type, int]):
        """
        初始化中间件管理器

        :param crawler: Crawler 实例
        :param middleware_configs: 中间件路径或类对象到优先级的映射字典
        """
        self.crawler = crawler
        self.settings = crawler.settings
        self.logger = get_logger(self.settings, self.__class__.__name__)
        self.middleware_configs = middleware_configs
        self.middlewares: list[tuple[BaseMiddleware, int]] = []

    def _load_middleware(self, middleware_path_or_cls: str | type, priority: int) -> BaseMiddleware | None:
        """
        加载并实例化中间件类

        :param middleware_path_or_cls: 中间件类的完整路径或类对象
        :param priority: 中间件的优先级
        :return: 中间件实例，如果加载失败则返回 None
        """
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
            return middleware
        except Exception as e:
            self.logger.error(f"Failed to load middleware {middleware_path_or_cls}: {e}")
            return None

    async def open(self):
        """
        加载并初始化所有中间件
        """
        # 加载中间件
        for middleware_path, priority in self.middleware_configs.items():
            middleware = self._load_middleware(middleware_path, priority)
            if middleware:
                self.middlewares.append((middleware, priority))

        # 按优先级排序（子类会以不同方式使用）
        self.middlewares.sort(key=lambda x: x[1])

        # 打开所有中间件
        for middleware, _ in self.middlewares:
            try:
                await middleware.open()
            except Exception as e:
                self.logger.error(f"Error opening middleware {middleware.__class__.__name__}: {e}")

    async def close(self):
        """
        关闭所有中间件
        """
        for middleware, _ in self.middlewares:
            try:
                await middleware.close()
            except Exception as e:
                self.logger.error(f"Error closing middleware {middleware.__class__.__name__}: {e}")


class DownloaderMiddlewareManager(MiddlewareManager):
    """
    下载器中间件管理器

    在下载前处理请求，在下载后处理响应
    """

    async def process_request(self, request: "Request", spider: "Spider") -> "Request | Response | None":
        """
        通过所有下载器中间件处理请求

        中间件按优先级升序调用

        :param request: 要处理的请求
        :param spider: 爬虫实例
        :return: Request、Response 或 None
        """
        # 按优先级升序处理（数字越小越先执行）
        for middleware, _ in self.middlewares:
            if not isinstance(middleware, DownloaderMiddleware):
                continue

            try:
                result = await middleware.process_request(request, spider)

                # 如果中间件返回 Response，停止并返回
                if result.__class__.__name__ == "Response":
                    self.logger.debug(
                        f"Middleware {middleware.__class__.__name__} returned Response, stopping request processing"
                    )
                    return result

                # 如果中间件返回 None，丢弃请求
                if result is None:
                    self.logger.debug(f"Middleware {middleware.__class__.__name__} dropped request: {request.url}")
                    return None

                # 否则，使用返回的请求传递给下一个中间件
                request = result

            except Exception as e:
                self.logger.error(f"Error in {middleware.__class__.__name__}.process_request for {request.url}: {e}")
                # 继续下一个中间件
                continue

        return request

    async def process_response(
        self, request: "Request", response: "Response", spider: "Spider"
    ) -> "Response | Request | None":
        """
        通过所有下载器中间件处理响应

        中间件按优先级降序调用（反向）

        :param request: 原始请求
        :param response: 要处理的响应
        :param spider: 爬虫实例
        :return: Response、Request（重试）或 None
        """
        # 按优先级降序处理（数字越大越先执行）
        for middleware, _ in reversed(self.middlewares):
            if not isinstance(middleware, DownloaderMiddleware):
                continue

            try:
                result = await middleware.process_response(request, response, spider)

                # 如果中间件返回 Request，表示要重试
                if result.__class__.__name__ == "Request":
                    self.logger.debug(f"Middleware {middleware.__class__.__name__} returned Request, will retry")
                    return result

                # 如果中间件返回 None，丢弃响应
                if result is None:
                    self.logger.debug(f"Middleware {middleware.__class__.__name__} dropped response for {request.url}")
                    return None

                # 否则，使用返回的响应传递给下一个中间件
                response = result

            except Exception as e:
                self.logger.error(f"Error in {middleware.__class__.__name__}.process_response for {request.url}: {e}")
                # 继续下一个中间件
                continue

        return response

    async def process_exception(
        self, request: "Request", exception: Exception, spider: "Spider"
    ) -> "Request | Response | None":
        """
        通过所有下载器中间件处理异常

        中间件按优先级降序调用（反向）

        :param request: 导致异常的请求
        :param exception: 引发的异常
        :param spider: 爬虫实例
        :return: Request（重试）、Response 或 None
        """
        # 按优先级降序处理（数字越大越先执行）
        for middleware, _ in reversed(self.middlewares):
            if not isinstance(middleware, DownloaderMiddleware):
                continue

            try:
                result = await middleware.process_exception(request, exception, spider)

                # 如果中间件返回 Request 或 Response，停止处理
                if result is not None:
                    self.logger.debug(f"Middleware {middleware.__class__.__name__} handled exception for {request.url}")
                    return result

            except Exception as e:
                self.logger.error(f"Error in {middleware.__class__.__name__}.process_exception for {request.url}: {e}")
                # 继续下一个中间件
                continue

        return None


class SpiderMiddlewareManager(MiddlewareManager):
    """
    爬虫中间件管理器

    处理爬虫输入/输出和起始请求
    """

    async def process_spider_input(self, response: "Response", spider: "Spider") -> bool:
        """
        在传递给爬虫回调前处理响应

        中间件按优先级升序调用

        :param response: 要处理的响应
        :param spider: 爬虫实例
        :return: 如果处理应该继续则返回 True，否则返回 False
        """
        # 按优先级升序处理（数字越小越先执行）
        for middleware, _ in self.middlewares:
            if not isinstance(middleware, SpiderMiddleware):
                continue

            try:
                await middleware.process_spider_input(response, spider)
            except Exception as e:
                self.logger.error(f"Error in {middleware.__class__.__name__}.process_spider_input: {e}")
                # 调用 process_spider_exception
                result = await self.process_spider_exception(response, e, spider)
                if result is not None:
                    return False
                # 如果没有中间件处理，重新抛出
                raise

        return True

    async def process_spider_output(
        self, response: "Response", result: AsyncGenerator, spider: "Spider"
    ) -> AsyncGenerator:
        """
        处理爬虫回调返回的结果

        中间件按优先级降序调用（反向）

        :param response: 已处理的响应
        :param result: 结果的异步生成器
        :param spider: 爬虫实例
        :return: Request 或 Item 对象
        """
        # 按优先级降序处理（数字越大越先执行）
        for middleware, _ in reversed(self.middlewares):
            if not isinstance(middleware, SpiderMiddleware):
                continue

            try:
                result = middleware.process_spider_output(response, result, spider)
            except Exception as e:
                self.logger.error(f"Error in {middleware.__class__.__name__}.process_spider_output: {e}")
                # 继续使用原始结果
                continue

        # 生成所有结果
        async for item in result:
            yield item

    async def process_spider_exception(
        self, response: "Response", exception: Exception, spider: "Spider"
    ) -> AsyncGenerator | None:
        """
        处理爬虫回调中的异常

        中间件按优先级降序调用（反向）

        :param response: 正在处理的响应
        :param exception: 引发的异常
        :param spider: 爬虫实例
        :return: 结果的异步生成器或 None
        """
        # 按优先级降序处理（数字越大越先执行）
        for middleware, _ in reversed(self.middlewares):
            if not isinstance(middleware, SpiderMiddleware):
                continue

            try:
                result = await middleware.process_spider_exception(response, exception, spider)
                if result is not None:
                    self.logger.debug(f"Middleware {middleware.__class__.__name__} handled spider exception")
                    return result
            except Exception as e:
                self.logger.error(f"Error in {middleware.__class__.__name__}.process_spider_exception: {e}")
                continue

        return None

    async def process_start_requests(self, start_requests: AsyncGenerator, spider: "Spider") -> AsyncGenerator:
        """
        处理起始请求生成器

        中间件按优先级降序调用（反向）

        :param start_requests: 起始请求生成器
        :param spider: 爬虫实例
        :return: Request 对象
        """
        # 按优先级降序处理（数字越大越先执行）
        for middleware, _ in reversed(self.middlewares):
            if not isinstance(middleware, SpiderMiddleware):
                continue

            try:
                start_requests = middleware.process_start_requests(start_requests, spider)
            except Exception as e:
                self.logger.error(f"Error in {middleware.__class__.__name__}.process_start_requests: {e}")
                # 继续使用原始生成器
                continue

        # 生成所有请求
        async for request in start_requests:
            yield request


class PipelineMiddlewareManager(MiddlewareManager):
    """
    管道中间件管理器

    在管道处理前后处理 Item
    """

    async def process_item_before(self, item: "Item", spider: "Spider") -> "Item | None":
        """
        在 Item 进入管道前处理

        中间件按优先级升序调用

        :param item: 要处理的 Item
        :param spider: 爬虫实例
        :return: Item 或 None（丢弃）
        """
        # 按优先级升序处理（数字越小越先执行）
        for middleware, _ in self.middlewares:
            if not isinstance(middleware, PipelineMiddleware):
                continue

            try:
                item = await middleware.process_item_before(item, spider)

                # 如果中间件返回 None，丢弃 Item
                if item is None:
                    self.logger.debug(f"Middleware {middleware.__class__.__name__} dropped item")
                    return None

            except Exception as e:
                self.logger.error(f"Error in {middleware.__class__.__name__}.process_item_before: {e}")
                # 继续下一个中间件
                continue

        return item

    async def process_item_after(self, item: "Item", spider: "Spider") -> "Item | None":
        """
        在 Item 离开管道后处理

        中间件按优先级降序调用（反向）

        :param item: 已处理的 Item
        :param spider: 爬虫实例
        :return: Item 或 None（丢弃）
        """
        # 按优先级降序处理（数字越大越先执行）
        for middleware, _ in reversed(self.middlewares):
            if not isinstance(middleware, PipelineMiddleware):
                continue

            try:
                item = await middleware.process_item_after(item, spider)

                # 如果中间件返回 None，丢弃 Item
                if item is None:
                    self.logger.debug(f"Middleware {middleware.__class__.__name__} dropped item")
                    return None

            except Exception as e:
                self.logger.error(f"Error in {middleware.__class__.__name__}.process_item_after: {e}")
                # 继续下一个中间件
                continue

        return item
