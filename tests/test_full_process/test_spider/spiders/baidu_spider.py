import typing
from collections.abc import AsyncGenerator
from typing import Any

from maize import Request, Spider, SpiderSettings
from tests.test_full_process.test_spider.items import BaiduItem

if typing.TYPE_CHECKING:
    from maize import Response


class BaiduSpider(Spider):
    async def start_requests(self) -> AsyncGenerator[Request, Any]:
        yield Request(url="http://www.baidu.com")

    async def open(self, settings: "SpiderSettings"):
        await super().open(settings)
        print("custom open")

    async def close(self):
        await super().close()
        print("custom close")

    @staticmethod
    async def get_headers():
        return {
            "Accept": "*/*",
            "Connection": "close",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
        }

    async def parse(self, response: "Response"):
        print(f"parse: {response}")
        for _i in range(1):
            url = "http://www.baidu.com"
            yield Request(url=url, callback=self.parse_page, headers_func=self.get_headers)

    @staticmethod
    async def parse_page(response: "Response"):
        li_list = response.xpath("//li[contains(@class, 'hotsearch-item')]")
        for li in li_list:
            item = BaiduItem()
            item.title = li.xpath(".//span[@class='title-content-title']/text()").get()
            item.url = li.xpath("./a/@href").get()
            yield item
