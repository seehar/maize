import asyncio
import typing

from playwright.async_api import Page

from maize import Request
from maize import Response
from maize import Spider


class RpaBaiduSpider(Spider):
    custom_settings = {
        "CONCURRENCY": 1,
        "DOWNLOADER": "maize.downloader.playwright_downloader.PlaywrightDownloader",
        "USE_SESSION": True,
    }

    async def start_requests(self) -> typing.AsyncGenerator[Request, typing.Any]:
        for _ in range(2):
            yield Request("https://www.baidu.com", cookies={})

    async def parse(self, response: Response[Page]):
        print(response.url)

        print("-" * 100)
        try:
            driver = response.driver
            await driver.goto("https://www.baidu.com/")
            await driver.wait_for_load_state()
            await asyncio.sleep(1)

            print("success:", driver.url)
        except Exception as e:
            print(e)
        finally:
            print("-" * 100)


if __name__ == "__main__":
    RpaBaiduSpider().run()
