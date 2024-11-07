import asyncio
import typing

from playwright.async_api import Page

from maize import CrawlerProcess
from maize import Request
from maize import Response
from maize import Spider
from maize.utils import CookieUtil


class RpaJdSpider(Spider):
    custom_settings = {
        "CONCURRENCY": 1,
        "DOWNLOADER": "maize.downloader.playwright_downloader.PlaywrightDownloader",
        "USE_SESSION": False,
    }

    async def start_requests(self) -> typing.AsyncGenerator[Request, typing.Any]:
        cookie_str = ""
        cookies = CookieUtil.str_cookies_to_list(cookie_str, ".jd.com")
        yield Request("https://item.jd.com/10075424349847.html", cookies=cookies)

    async def parse(self, response: Response[Page]):
        print(response.text)


async def main():
    process = CrawlerProcess()
    await process.crawl(RpaJdSpider)
    await process.start()


if __name__ == "__main__":
    asyncio.run(main())
