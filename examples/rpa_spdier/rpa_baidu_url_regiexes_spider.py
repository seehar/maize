import typing

from playwright.async_api import Page

from maize import Request
from maize import Response
from maize import Spider
from maize.downloader.playwright_downloader import PlaywrightDownloader


class RpaBaiduSpider(Spider):
    custom_settings = {
        "CONCURRENCY": 1,
        "DOWNLOADER": "maize.downloader.playwright_downloader.PlaywrightDownloader",
        "USE_SESSION": True,
        "RPA_URL_REGEXES": ["https://www.baidu.com/sugrec"],
    }

    async def start_requests(self) -> typing.AsyncGenerator[Request, typing.Any]:
        for _ in range(2):
            yield Request("https://www.baidu.com", cookies={})

    async def parse(self, response: Response[PlaywrightDownloader, Page]):
        print(response.url)

        print("-" * 100)
        text = response.driver.get_text("https://www.baidu.com/sugrec")
        print(text)
        print("-" * 100)


if __name__ == "__main__":
    RpaBaiduSpider().run()
