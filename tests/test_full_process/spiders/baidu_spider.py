from maize import Request
from maize import Spider
from tests.test_full_process.items import BaiduItem


class BaiduSpider(Spider):
    start_urls = ["http://www.baidu.com", "http://www.baidu.com"]

    async def parse(self, response):
        print(f"parse: {response}")
        for i in range(1):
            url = "http://www.baidu.com"
            yield Request(url=url, callback=self.parse_page)

    async def parse_page(self, response):
        print(f"parse_page: {response}")
        for i in range(1):
            url = "http://www.baidu.com"
            yield Request(url=url, callback=self.parse_detail)

    async def parse_detail(self, response):
        # print(response.text)
        print(f"parse_detail: {response}")
        item = BaiduItem()
        item["url"] = "https://www.baidu.com"
        item["title"] = "百度一下"
        yield item
