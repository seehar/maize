import asyncio
from typing import TYPE_CHECKING
from typing import Any
from typing import AsyncGenerator
from typing import List
from typing import Optional

from maize.common.http import Response
from maize.common.http.request import Request
from maize.core.crawler import CrawlerProcess


if TYPE_CHECKING:
    from maize.core.crawler import Crawler


class Spider:
    __spider_type__: str = "spider"
    start_urls: List[str] = []
    start_url: Optional[str] = None

    custom_settings: dict

    def __init__(self):
        if not hasattr(self, "start_urls"):
            self.start_urls = []

        self.crawler: Optional["Crawler"] = None

    def __str__(self):
        return self.__class__.__name__

    async def open(self):
        """
        在 Spider 启动时执行一些初始化操作
        :return:
        """

    async def close(self):
        """
        在 Spider 关闭时执行一些清理操作
        :return:
        """

    @classmethod
    def create_instance(cls, crawler: "Crawler"):
        instance = cls()
        instance.crawler = crawler
        return instance

    async def start_requests(self) -> AsyncGenerator[Request, Any]:
        if self.start_urls:
            for url in self.start_urls:
                yield Request(url=url)

        elif self.start_url and isinstance(self.start_url, str):
            yield Request(url=self.start_url)

    async def parse(self, response: Response):
        raise NotImplementedError

    async def _async_run(self):
        process = CrawlerProcess()
        await process.crawl(self)
        await process.start()

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self._async_run())
