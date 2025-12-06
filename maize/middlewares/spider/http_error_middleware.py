"""
HTTP 错误中间件

根据 HTTP 状态码过滤响应
"""

from typing import TYPE_CHECKING

from maize.common.constant import LogLevelEnum
from maize.middlewares.base_middleware import SpiderMiddleware

if TYPE_CHECKING:
    from maize.common.http.response import Response
    from maize.spider.spider import Spider


# 被认为是成功的状态码
HTTP_SUCCESS_CODES = list(range(200, 300))


class HttpErrorMiddleware(SpiderMiddleware):
    """
    HTTP 错误响应过滤中间件

    可以配置为:
    - 仅允许特定的状态码
    - 阻止特定的状态码
    - 记录错误日志以便监控

    配置项:
        - http_error_allowed_codes: 允许的状态码列表（默认: 200-299）
        - http_error_denied_codes: 拒绝的状态码列表（优先级高于允许列表）
        - http_error_log_level: 错误日志级别（'debug', 'info', 'warning', 'error'）
    """

    async def open(self):
        pass

    def __init__(
        self, settings=None, allowed_codes=None, denied_codes=None, log_level: str = LogLevelEnum.WARNING.value
    ):
        """
        初始化 HTTP 错误中间件

        :param settings: 爬虫配置
        :param allowed_codes: 允许的状态码列表
        :param denied_codes: 拒绝的状态码列表
        :param log_level: 错误日志级别
        """
        super().__init__(settings)
        self.allowed_codes = allowed_codes or HTTP_SUCCESS_CODES
        self.denied_codes = denied_codes or []
        self.log_level = log_level

        # 统计信息跟踪
        self.stats = {}

    @classmethod
    def from_crawler(cls, crawler):
        """
        从 crawler 创建中间件实例

        :param crawler: Crawler 实例
        :return: HttpErrorMiddleware 实例
        """
        settings = crawler.settings

        allowed_codes = getattr(settings, "http_error_allowed_codes", None)
        denied_codes = getattr(settings, "http_error_denied_codes", None)
        log_level = getattr(settings, "http_error_log_level", "warning")

        return cls(settings, allowed_codes=allowed_codes, denied_codes=denied_codes, log_level=log_level)

    def _should_filter(self, response: "Response") -> bool:
        """
        检查响应是否应该被过滤

        :param response: 响应实例
        :return: 如果响应应该被过滤返回 True
        """
        status = response.status

        # 首先检查拒绝的状态码（优先级更高）
        if self.denied_codes and status in self.denied_codes:
            return True

        # 检查允许的状态码
        return bool(self.allowed_codes and status not in self.allowed_codes)

    def _log_error(self, response: "Response"):
        """
        记录 HTTP 错误

        :param response: 响应实例
        """
        status = response.status
        url = response.url

        # 更新统计信息
        stat_key = f"http_error_{status}"
        self.stats[stat_key] = self.stats.get(stat_key, 0) + 1

        # 日志消息
        message = f"HTTP {status} error for {url}"

        if self.log_level == LogLevelEnum.DEBUG.value:
            self.logger.debug(message)
        elif self.log_level == LogLevelEnum.INFO.value:
            self.logger.info(message)
        elif self.log_level == LogLevelEnum.WARNING.value:
            self.logger.warning(message)
        elif self.log_level == LogLevelEnum.ERROR.value:
            self.logger.error(message)

    async def process_spider_input(self, response: "Response", spider: "Spider") -> None:
        """
        在传递给爬虫前检查响应状态码

        :param response: 响应实例
        :param spider: 爬虫实例
        :raises Exception: 如果状态码应该被过滤
        """
        if self._should_filter(response):
            self._log_error(response)
            # 抛出异常以触发 process_spider_exception
            raise Exception(f"HTTP {response.status} error")

    async def close(self):
        """
        关闭时记录统计信息
        """
        if self.stats:
            self.logger.info("HTTP Error Statistics:")
            for stat, count in sorted(self.stats.items()):
                self.logger.info(f"  {stat}: {count}")
