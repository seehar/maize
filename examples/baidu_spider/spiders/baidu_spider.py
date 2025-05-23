from typing import Any
from typing import AsyncGenerator

from examples.baidu_spider.items import BaiduItem
from maize import Request
from maize import Response
from maize import Spider


class BaiduSpider(Spider):
    custom_settings = {
        "LOGGER_HANDLER": "examples.baidu_spider.logger_util.InterceptHandler",
        "RANDOM_WAIT_TIME": (10, 15),
    }

    async def start_requests(self) -> AsyncGenerator[Request, Any]:
        yield Request(url="http://www.baidu.com")

    async def parse(self, response: Response):
        li_list = response.xpath("//li[contains(@class, 'hotsearch-item')]")
        for li in li_list:
            item = BaiduItem()
            item["title"] = li.xpath(".//span[@class='title-content-title']/text()").get()
            item["url"] = li.xpath("./a/@href").get()
            yield item

        for i in range(10):
            url = "http://www.baidu111.com"
            yield Request(url=url, callback=self.parse_detail)

    @staticmethod
    async def parse_detail(response: Response):
        li_list = response.xpath("//li[contains(@class, 'hotsearch-item')]")
        for li in li_list:
            item = BaiduItem()
            item["title"] = li.xpath(".//span[@class='title-content-title']/text()").get()
            item["url"] = li.xpath("./a/@href").get()
            yield item
