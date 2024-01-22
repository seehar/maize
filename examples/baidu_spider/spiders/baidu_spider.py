from maize import Request
from maize import Response
from maize import Spider
from tests.test_full_process.items import BaiduItem


class BaiduSpider(Spider):
    start_urls = ["http://www.baidu.com", "http://www.baidu.com"]

    async def parse(self, response: Response):
        li_list = response.xpath("//li[contains(@class, 'hotsearch-item')]")
        for li in li_list:
            item = BaiduItem()
            item["title"] = li.xpath(
                ".//span[@class='title-content-title']/text()"
            ).get()
            item["url"] = li.xpath("./a/@href").get()
            yield item

        for i in range(10):
            url = "http://www.baidu.com"
            yield Request(url=url, callback=self.parse_detail)

    @staticmethod
    async def parse_detail(response: Response):
        li_list = response.xpath("//li[contains(@class, 'hotsearch-item')]")
        for li in li_list:
            item = BaiduItem()
            item["title"] = li.xpath(
                ".//span[@class='title-content-title']/text()"
            ).get()
            item["url"] = li.xpath("./a/@href").get()
            yield item
