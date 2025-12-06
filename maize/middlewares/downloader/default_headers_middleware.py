"""
默认请求头中间件

为所有请求添加默认的 HTTP 请求头
"""

from typing import TYPE_CHECKING

from maize.middlewares.base_middleware import DownloaderMiddleware

if TYPE_CHECKING:
    from maize.common.http.request import Request
    from maize.spider.spider import Spider


DEFAULT_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
}


class DefaultHeadersMiddleware(DownloaderMiddleware):
    """
    默认请求头中间件

    仅在请求中尚未存在时添加请求头

    配置项:
        - default_headers: 要添加的请求头字典（可选）
    """

    async def open(self):
        pass

    async def close(self):
        pass

    def __init__(self, settings=None, default_headers=None):
        """
        初始化默认请求头中间件

        :param settings: 爬虫配置
        :param default_headers: 自定义默认请求头字典
        """
        super().__init__(settings)
        self.default_headers = default_headers or DEFAULT_HEADERS.copy()

    @classmethod
    def from_crawler(cls, crawler):
        """
        从 crawler 创建中间件实例

        :param crawler: Crawler 实例
        :return: DefaultHeadersMiddleware 实例
        """
        settings = crawler.settings

        # 尝试从配置中获取默认请求头
        default_headers = getattr(settings, "default_headers", None)

        return cls(settings, default_headers=default_headers)

    async def process_request(self, request: "Request", spider: "Spider") -> "Request":
        """
        为请求添加默认请求头

        :param request: 要处理的请求
        :param spider: 爬虫实例
        :return: 修改后的请求
        """
        # 如果请求头不存在则初始化
        if not request.headers:
            request.headers = {}

        # 添加默认请求头（如果尚未存在）
        for header, value in self.default_headers.items():
            if header not in request.headers:
                request.headers[header] = value

        return request
