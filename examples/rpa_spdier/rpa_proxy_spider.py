import typing

from playwright.async_api import Page

from maize import Request
from maize import Response
from maize import Spider


class RpaJdSpider(Spider):
    custom_settings = {
        "CONCURRENCY": 1,
        "DOWNLOADER": "maize.downloader.playwright_downloader.PlaywrightDownloader",
        "USE_SESSION": False,
        "RPA_DRIVER_TYPE": "chromium",
        "PROXY_TUNNEL": "172.19.214.194:7890",
    }

    async def start_requests(self) -> typing.AsyncGenerator[Request, typing.Any]:
        yield Request("https://icanhazip.com")

    async def parse(self, response: Response[None, Page]):
        print(response.text)


if __name__ == "__main__":
    RpaJdSpider().run()
