import asyncio
import logging
import typing
from abc import abstractmethod
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

import aiohttp

from maize.base.interface.lite_spider_interface import LiteSpiderInterface
from maize.common.http import Request, Response

if TYPE_CHECKING:
    pass


# 创建简单的 logger
_logger = logging.getLogger("maize.lite")


class LiteSpider(LiteSpiderInterface):
    """Lite 版本的爬虫 - 简化实现，内置简单 HTTP 下载"""

    def __init__(self):
        super().__init__()
        self._session: aiohttp.ClientSession | None = None
        self._crawler: LiteCrawler | None = None
        self._logger = logging.getLogger(f"maize.lite.{self.__class__.__name__}")

    @property
    def logger(self) -> logging.Logger:
        """返回爬虫的 logger"""
        return self._logger

    async def open(self) -> None:
        """爬虫启动时调用，可用于初始化资源"""
        self._session = aiohttp.ClientSession()

    async def close(self) -> None:
        """爬虫关闭时调用，可用于清理资源"""
        if self._session:
            await self._session.close()
            self._session = None

    async def fetch(self, request: Request) -> Response:
        """执行 HTTP 请求"""
        if not self._session:
            raise RuntimeError("Session not initialized. Did you call open()?")

        try:
            headers = await request.get_headers()
            async with self._session.request(
                method=request.method,
                url=request.url,
                headers=headers,
                data=request.data,
                json=request.json,
                params=request.params,
                cookies=request.cookies,
                allow_redirects=request.follow_redirects,
                max_redirects=request.max_redirects,
            ) as response:
                body = await response.read()
                return Response(
                    url=str(response.url),
                    headers=dict(response.headers.items()),
                    status=response.status,
                    body=body,
                    request=request,
                    source_response=response,
                )
        except Exception as e:
            self.logger.error(f"Request failed: {request.url}, error: {e}")
            return Response(
                url=request.url,
                headers={},
                status=0,
                body=b"",
                request=request,
            )

    @abstractmethod
    async def start_requests(self) -> AsyncGenerator[Request, typing.Any]:
        """生成初始请求 - 子类必须实现"""
        ...

    @abstractmethod
    async def parse(self, response: Response) -> None:
        """解析响应 - 子类必须实现"""
        ...

    async def crawl(self) -> None:
        """执行爬虫的主要逻辑"""
        await self.open()

        try:
            async for request in self.start_requests():
                response = await self.fetch(request)
                await self.parse(response)
        finally:
            await self.close()

    def set_crawler(self, crawler: "LiteCrawler") -> None:
        """设置爬虫运行器"""
        self._crawler = crawler


class LiteCrawler:
    """Lite 版本的爬虫运行器"""

    def __init__(self, spider_cls: type[LiteSpider], settings: "LiteSettings | None" = None):
        self.spider_cls = spider_cls
        self.spider: LiteSpider | None = None
        self.settings = settings or LiteSettings()

    async def crawl(self) -> None:
        """运行爬虫"""
        spider = self.spider_cls()
        self.spider = spider
        await spider.open()

        try:
            async for request in spider.start_requests():
                response = await spider.fetch(request)
                await spider.parse(response)
        finally:
            await spider.close()

    @staticmethod
    def idle() -> bool:
        """检查爬虫是否空闲"""
        return True


class LiteCrawlerProcess:
    """Lite 版本的爬虫进程管理器 - 管理多个爬虫"""

    def __init__(self, settings: "LiteSettings | None" = None):
        self.crawlers: list[LiteCrawler] = []
        self.settings = settings or LiteSettings()

    async def crawl(self, spider_cls: type[LiteSpider]) -> None:
        """添加并运行一个爬虫"""
        crawler = LiteCrawler(spider_cls, self.settings)
        self.crawlers.append(crawler)
        await crawler.crawl()

    async def start(self) -> None:
        """启动所有爬虫（Lite 版本串行执行）"""
        for crawler in self.crawlers:
            await crawler.crawl()

    def run(self, spider_cls: type[LiteSpider] | None = None) -> None:
        """同步运行入口"""
        if spider_cls:
            asyncio.run(self.crawl(spider_cls))
        else:
            asyncio.run(self._run())

    async def _run(self) -> None:
        """异步运行（启动所有已添加的爬虫）"""
        for crawler in self.crawlers:
            await crawler.crawl()


class LiteSettings:
    """Lite 版本的设置 - 简化版"""

    def __init__(
        self,
        request_timeout: float = 30.0,
        max_retries: int = 3,
        follow_redirects: bool = True,
        max_redirects: int = 10,
        verify_ssl: bool = True,
        log_level: str = "INFO",
    ):
        self.request_timeout = request_timeout
        self.max_retries = max_retries
        self.follow_redirects = follow_redirects
        self.max_redirects = max_redirects
        self.verify_ssl = verify_ssl
        self.log_level = log_level
