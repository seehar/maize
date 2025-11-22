import asyncio
import typing

from playwright.async_api import Page

from maize import Request, Response, Spider, SpiderSettings
from maize.common.constant import SpiderDownloaderEnum
from maize.downloader.patchright_downloader import PatchrightDownloader


class RpaBaiduSpider(Spider):
    async def start_requests(self) -> typing.AsyncGenerator[Request, typing.Any]:
        for _ in range(2):
            yield Request("https://www.baidu.com", cookies={})

    async def parse(self, response: Response[PatchrightDownloader, Page]):
        self.logger.info(response.url)

        self.logger.info("-" * 100)
        try:
            async with response.driver.get_page() as page:
                await page.goto("https://www.baidu.com/")
                await page.wait_for_load_state()
                await asyncio.sleep(1)

                self.logger.info(f"success: {page.url}")
        except Exception as e:
            self.logger.error(e)
        finally:
            self.logger.info("-" * 100)


if __name__ == "__main__":
    spider_settings = SpiderSettings()
    spider_settings.concurrency = 1
    spider_settings.downloader = SpiderDownloaderEnum.PATCHRIGHT.value
    spider_settings.request.use_session = True

    RpaBaiduSpider().run(spider_settings)
