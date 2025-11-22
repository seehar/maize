import typing

from playwright.async_api import Page

from maize import Request, Response, Spider, SpiderSettings
from maize.common.constant import RPADriverTypeEnum, SpiderDownloaderEnum


class RpaJdSpider(Spider):
    async def start_requests(self) -> typing.AsyncGenerator[Request, typing.Any]:
        yield Request("https://item.jd.com/10075424349847.html")

    async def parse(self, response: Response[None, Page]):
        self.logger.info(response.text)


if __name__ == "__main__":
    spider_settings = SpiderSettings()
    spider_settings.concurrency = 1
    spider_settings.downloader = SpiderDownloaderEnum.PLAYWRIGHT.value
    spider_settings.rpa.endpoint_url = "http://localhost:9222"
    spider_settings.request.use_session = False
    spider_settings.rpa.driver_type = RPADriverTypeEnum.CHROMIUM.value

    RpaJdSpider().run(spider_settings)
