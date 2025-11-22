from collections.abc import AsyncGenerator
from typing import Any

from examples.baidu_spider.items import BaiduItem
from maize import Request, Response, Spider, SpiderSettings


class PauseAndProceedSpider(Spider):
    async def start_requests(self) -> AsyncGenerator[Request, Any]:
        for _i in range(2):
            yield Request(
                url="http://www.baidu.com",
                priority=1,
                error_callback=self.error_callback,
            )

    async def parse(self, response: Response):
        li_list = response.xpath("//li[contains(@class, 'hotsearch-item')]")
        for li in li_list:
            item = BaiduItem()
            item.title = li.xpath(".//span[@class='title-content-title']/text()").get()
            item.url = li.xpath("./a/@href").get()
            self.logger.info(item.model_dump())
            yield item

        if li_list:
            if self.is_pause():
                self.logger.warning(f"爬虫已暂停，无需重复 {self.gte_priority=}")
                return

            yield Request(
                url="http://www.baidu.com",
                callback=self.parse_bing,
                priority=99,
                error_callback=self.bing_error,
            )
            await self.pause_spider(lte_priority=0)
            self.logger.warning(f"爬虫已暂停 {self.gte_priority=}")
            yield Request(
                url="http://www.baidu.com",
                callback=self.parse_bing,
                priority=99,
                error_callback=self.bing_error,
            )

    async def error_callback(self, request: Request):
        self.logger.info(request)
        if not self.is_pause():
            yield Request(
                url="http://www.baidu.com",
                callback=self.parse_bing,
                priority=99,
                error_callback=self.bing_error,
            )
            await self.pause_spider(lte_priority=0)
            self.logger.warning(f"爬虫已暂停 {self.gte_priority=}")

    async def parse_detail(self, response: Response):
        self.logger.info(f"{self.gte_priority=}")
        li_list = response.xpath("//li[contains(@class, 'hotsearch-item')]")
        for li in li_list:
            item = BaiduItem()
            item.title = li.xpath(".//span[@class='title-content-title']/text()").get()
            item.url = li.xpath("./a/@href").get()
            self.logger.info(item.model_dump())
            yield item

    async def parse_bing(self, response: Response):
        self.logger.info(response)
        await self.proceed_spider()
        self.logger.warning(f"爬虫已继续 {self.gte_priority=}")

        for _i in range(2):
            url = "http://www.baidu.com"
            yield Request(url=url, callback=self.parse_detail, priority=1)

    async def bing_error(self, request: Request):
        self.logger.info(request)
        if self.is_pause():
            await self.proceed_spider()
            self.logger.warning(f"爬虫已继续 {self.gte_priority=}")
        else:
            self.logger.warning(f"爬虫无需继续 {self.gte_priority=}")


if __name__ == "__main__":
    spider_settings = SpiderSettings()
    spider_settings.logger_handler = "examples.baidu_spider.logger_util.InterceptHandler"
    spider_settings.request.request_timeout = 1
    spider_settings.concurrency = 1
    PauseAndProceedSpider().run(spider_settings)
