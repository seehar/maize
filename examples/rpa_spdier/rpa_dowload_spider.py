import asyncio
import typing

from playwright.async_api import Page

from maize import Request, Response, Spider, SpiderSettings
from maize.common.constant import SpiderDownloaderEnum
from maize.downloader.playwright_downloader import PlaywrightDownloader


class RpaDownloadSpider(Spider):
    async def start_requests(self) -> typing.AsyncGenerator[Request, typing.Any]:
        yield Request("https://image.baidu.com/")

    async def parse(self, response: Response[PlaywrightDownloader, Page]):
        async with response.driver.get_page() as page:
            await page.wait_for_load_state()
            await asyncio.sleep(1)

            div = await page.query_selector("//div[contains(@class, 'item-img-wrap')]")
            bounding_box = await div.bounding_box()
            start_x = bounding_box["x"]
            start_y = bounding_box["y"]
            await page.mouse.move(start_x + 23, start_y + 23)
            await asyncio.sleep(0.5)

            button = await page.query_selector(
                "//div[contains(@class, 'item-img-wrap')]/div/div[contains(@class, 'item-info')]/div/div[contains(@class, 'download-btn')]"
            )
            await button.click()
            await asyncio.sleep(1)


if __name__ == "__main__":
    spider_settings = SpiderSettings()
    spider_settings.concurrency = 1
    spider_settings.downloader = SpiderDownloaderEnum.PLAYWRIGHT.value
    spider_settings.request.use_session = True
    spider_settings.rpa.download_path = r"C:\Users\seehar\Desktop\temp\rpa"
    spider_settings.rpa.headless = False

    RpaDownloadSpider().run(spider_settings)
