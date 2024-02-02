import typing

from maize import Request
from maize import Spider
from tests.test_full_process.test_spider.items import BaiduItem


if typing.TYPE_CHECKING:
    from maize import Response


class BaiduSpider(Spider):
    start_urls = ["http://www.baidu.com", "http://www.baidu.com"]

    async def open(self):
        print("custom open")

    async def close(self):
        print("custom close")

    async def parse(self, response: "Response"):
        print(f"parse: {response}")
        for i in range(1):
            url = "http://www.baidu.com"
            yield Request(url=url, callback=self.parse_page)

    @staticmethod
    async def parse_page(response: "Response"):
        li_list = response.xpath("//li[contains(@class, 'hotsearch-item')]")
        for li in li_list:
            item = BaiduItem()
            item["title"] = li.xpath(
                ".//span[@class='title-content-title']/text()"
            ).get()
            item["url"] = li.xpath("./a/@href").get()
            yield item
