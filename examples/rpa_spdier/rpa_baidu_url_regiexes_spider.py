import typing

from playwright.async_api import Page

from maize import Request, Response, Spider, SpiderSettings
from maize.common.constant import SpiderDownloaderEnum
from maize.downloader.playwright_downloader import PlaywrightDownloader


class RpaBaiduSpider(Spider):
    async def start_requests(self) -> typing.AsyncGenerator[Request, typing.Any]:
        for _ in range(2):
            yield Request("https://www.baidu.com", cookies={})

    async def parse(self, response: Response[PlaywrightDownloader, Page]):
        self.logger.info(response.url)

        self.logger.info("-" * 100)
        text = response.driver.get_text("https://www.baidu.com/sugrec")
        self.logger.info(text)
        self.logger.info("-" * 100)


if __name__ == "__main__":
    spider_settings = SpiderSettings()
    spider_settings.concurrency = 1
    spider_settings.downloader = SpiderDownloaderEnum.PLAYWRIGHT.value
    spider_settings.request.use_session = True
    spider_settings.rpa.url_regexes = ["https://www.baidu.com/sugrec"]

    RpaBaiduSpider().run(spider_settings)
