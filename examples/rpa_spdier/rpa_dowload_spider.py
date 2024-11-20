import asyncio
import typing

from playwright.async_api import Page

from maize import Request
from maize import Response
from maize import Spider


class RpaDownloadSpider(Spider):
    custom_settings = {
        "CONCURRENCY": 1,
        "DOWNLOADER": "maize.downloader.playwright_downloader.PlaywrightDownloader",
        "USE_SESSION": True,
        "RPA_DOWNLOAD_PATH": r"C:\Users\EDY\Desktop\temp\rpa",
        "RPA_HEADLESS": False,
    }

    async def start_requests(self) -> typing.AsyncGenerator[Request, typing.Any]:
        yield Request("https://image.baidu.com/")

    async def parse(self, response: Response[Page]):
        driver = response.driver
        await driver.wait_for_load_state()
        await asyncio.sleep(1)

        div = await driver.query_selector("//div[contains(@class, 'item-img-wrap')]")
        bounding_box = await div.bounding_box()
        start_x = bounding_box["x"]
        start_y = bounding_box["y"]
        await driver.mouse.move(start_x + 23, start_y + 23)
        await asyncio.sleep(0.5)

        button = await driver.query_selector(
            f"//div[contains(@class, 'item-img-wrap')]/div/div[contains(@class, 'item-info')]/div/div[contains(@class, 'download-btn')]"
        )
        await button.click()
        await asyncio.sleep(1)


if __name__ == "__main__":
    RpaDownloadSpider().run()
