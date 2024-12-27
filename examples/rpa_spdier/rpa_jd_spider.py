import typing

from playwright.async_api import Page

from maize import Request
from maize import Response
from maize import Spider


class RpaJdSpider(Spider):
    custom_settings = {
        "CONCURRENCY": 1,
        "DOWNLOADER": "maize.downloader.playwright_downloader.PlaywrightDownloader",
        # .\chrome.exe --remote-debugging-port=9222
        "RPA_ENDPOINT_URL": "http://localhost:9222",
        "USE_SESSION": False,
        "RPA_DRIVER_TYPE": "chromium",
    }

    async def start_requests(self) -> typing.AsyncGenerator[Request, typing.Any]:
        # cookie_str = ""
        # cookies = CookieUtil.str_cookies_to_list(cookie_str, ".jd.com")
        yield Request("https://item.jd.com/10075424349847.html")

    async def parse(self, response: Response[Page]):
        print(response.text)


if __name__ == "__main__":
    RpaJdSpider().run()
