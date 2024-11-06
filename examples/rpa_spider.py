import asyncio
import typing

from maize import CrawlerProcess
from maize import Request
from maize import Spider


class BaiduSpider(Spider):
    # start_url = "http://www.baidu.com"

    custom_settings = {
        "CONCURRENCY": 2,
        "DOWNLOADER": "maize.downloader.playwright_downloader.PlaywrightDownloader",
    }

    async def start_requests(self) -> typing.AsyncGenerator[Request, typing.Any]:
        for _ in range(10):
            yield Request("https://www.baidu.com")

    def parse(self, response):
        print(response.text)


async def main():
    process = CrawlerProcess()
    await process.crawl(BaiduSpider)
    await process.start()


if __name__ == "__main__":
    asyncio.run(main())
