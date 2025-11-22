import typing

from playwright.async_api import Page

from maize import Request, Response, Spider, SpiderSettings
from maize.common.constant import RPADriverTypeEnum, SpiderDownloaderEnum


class RpaJdSpider(Spider):
    async def start_requests(self) -> typing.AsyncGenerator[Request, typing.Any]:
        yield Request("https://icanhazip.com")

    async def parse(self, response: Response[None, Page]):
        print(response.text)


if __name__ == "__main__":
    spider_settings = SpiderSettings()
    spider_settings.concurrency = 1
    spider_settings.downloader = SpiderDownloaderEnum.PLAYWRIGHT.value
    spider_settings.request.use_session = False
    spider_settings.rpa.driver_type = RPADriverTypeEnum.CHROMIUM.value
    spider_settings.proxy.proxy_url = "172.19.214.194:7890"

    RpaJdSpider().run(spider_settings)
