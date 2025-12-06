"""
重试中间件

根据各种条件处理请求重试
"""

import asyncio
from typing import TYPE_CHECKING

from maize.middlewares.base_middleware import DownloaderMiddleware

if TYPE_CHECKING:
    from maize.common.http.request import Request
    from maize.common.http.response import Response
    from maize.spider.spider import Spider


# 应该触发重试的状态码
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]


class RetryMiddleware(DownloaderMiddleware):
    """
    失败请求重试中间件

    根据以下条件重试请求:
    - HTTP 状态码
    - 下载过程中的异常
    - 最大重试次数

    配置项:
        - max_retry_count: 最大重试次数（默认: 3）
        - retry_http_codes: 需要重试的 HTTP 状态码列表（默认: [500, 502, 503, 504, 408, 429]）
        - retry_exceptions: 需要重试的异常类型列表（可选）
        - retry_delay: 重试之间的延迟秒数（默认: 0）
        - exponential_backoff: 是否使用指数退避延迟（默认: False）
    """

    async def open(self):
        pass

    async def close(self):
        pass

    def __init__(
        self,
        settings=None,
        max_retry_count=3,
        retry_http_codes=None,
        retry_exceptions=None,
        retry_delay=0,
        exponential_backoff=False,
    ):
        """
        初始化重试中间件

        :param settings: 爬虫配置
        :param max_retry_count: 最大重试尝试次数
        :param retry_http_codes: 触发重试的 HTTP 状态码
        :param retry_exceptions: 触发重试的异常类型
        :param retry_delay: 重试之间的基础延迟
        :param exponential_backoff: 是否使用指数退避
        """
        super().__init__(settings)
        self.max_retry_count = max_retry_count
        self.retry_http_codes = retry_http_codes or RETRY_HTTP_CODES
        self.retry_exceptions = retry_exceptions or [Exception]
        self.retry_delay = retry_delay
        self.exponential_backoff = exponential_backoff

    @classmethod
    def from_crawler(cls, crawler):
        """
        从 crawler 创建中间件实例

        :param crawler: Crawler 实例
        :return: RetryMiddleware 实例
        """
        settings = crawler.settings

        max_retry_count = getattr(settings.request, "max_retry_count", 3)
        retry_http_codes = getattr(settings, "retry_http_codes", None)
        retry_exceptions = getattr(settings, "retry_exceptions", None)
        retry_delay = getattr(settings, "retry_delay", 0)
        exponential_backoff = getattr(settings, "exponential_backoff", False)

        return cls(
            settings,
            max_retry_count=max_retry_count,
            retry_http_codes=retry_http_codes,
            retry_exceptions=retry_exceptions,
            retry_delay=retry_delay,
            exponential_backoff=exponential_backoff,
        )

    def _get_retry_count(self, request: "Request") -> int:
        """
        从请求的 meta 中获取当前重试次数

        :param request: 请求实例
        :return: 重试次数
        """
        if not request.meta:
            return 0
        return request.meta.get("retry_count", 0)

    def _set_retry_count(self, request: "Request", count: int):
        """
        在请求的 meta 中设置重试次数

        :param request: 请求实例
        :param count: 重试次数
        """
        if not request.meta:
            request._meta = {}
        request._meta["retry_count"] = count

    async def _calculate_delay(self, retry_count: int) -> float:
        """
        计算重试前的延迟时间

        :param retry_count: 当前重试次数
        :return: 延迟秒数
        """
        if not self.retry_delay:
            return 0

        if self.exponential_backoff:
            # 使用指数退避策略计算延迟
            return self.retry_delay * (2**retry_count)
        return self.retry_delay

    async def _retry_request(self, request: "Request", reason: str, spider: "Spider") -> "Request | None":
        """
        如果在重试限制内则创建重试请求

        :param request: 原始请求
        :param reason: 重试原因
        :param spider: 爬虫实例
        :return: 用于重试的新请求，如果超过最大重试次数则返回 None
        """
        retry_count = self._get_retry_count(request)

        if retry_count >= self.max_retry_count:
            self.logger.debug(f"Giving up on {request.url} after {retry_count} retries. Reason: {reason}")
            return None

        retry_count += 1
        self._set_retry_count(request, retry_count)

        # 计算并应用延迟
        delay = await self._calculate_delay(retry_count)
        if delay > 0:
            await asyncio.sleep(delay)

        self.logger.debug(f"Retrying {request.url} (attempt {retry_count}/{self.max_retry_count}). Reason: {reason}")

        return request

    async def process_response(
        self, request: "Request", response: "Response", spider: "Spider"
    ) -> "Response | Request | None":
        """
        检查响应状态码，如果需要则重试

        :param request: 请求实例
        :param response: 响应实例
        :param spider: 爬虫实例
        :return: Response、Request（重试）或 None
        """
        # 检查状态码是否应该触发重试
        if response.status in self.retry_http_codes:
            return await self._retry_request(request, f"HTTP {response.status}", spider)

        return response

    async def process_exception(self, request: "Request", exception: Exception, spider: "Spider") -> "Request | None":
        """
        如果异常匹配重试条件则重试请求

        :param request: 请求实例
        :param exception: 异常实例
        :param spider: 爬虫实例
        :return: Request（重试）或 None
        """
        # 检查异常类型是否应该触发重试
        for exc_type in self.retry_exceptions:
            if isinstance(exception, exc_type):
                return await self._retry_request(request, f"{exception.__class__.__name__}: {exception!s}", spider)

        return None
