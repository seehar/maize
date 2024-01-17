from maize import Request
from maize.core.spider.spider import Spider
from tests.baidu_spider.items import BaiduItem


class BaiduSpider2(Spider):
    start_urls = ["https://www.baidu.com", "https://www.baidu.com"]

    # custom_settings = {"CONCURRENCY": 8}

    async def parse(self, response):
        print(f"parse222: {response}")
        for i in range(10):
            url = "https://www.baidu.com"
            yield Request(url=url, callback=self.parse_page)

    async def parse_page(self, response):
        print(f"parse_page222: {response}")
        for i in range(10):
            url = "https://www.baidu.com"
            yield Request(url=url, callback=self.parse_detail)

    async def parse_detail(self, response):
        print(f"parse_detail222: {response}")
        item = BaiduItem()
        item["url"] = "https://www.baidu.com2"
        item["title"] = "百度一下2"
        yield item
