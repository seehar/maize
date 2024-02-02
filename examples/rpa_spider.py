import asyncio

from maize import CrawlerProcess
from maize import Spider


class BaiduSpider(Spider):
    start_url = "http://www.baidu.com"

    custom_settings = {
        "DOWNLOADER": "maize.core.downloader.playwright_downloader.PlaywrightDownloader"
    }

    def parse(self, response):
        print(response.text)


async def main():
    process = CrawlerProcess()
    await process.crawl(BaiduSpider)
    await process.start()


if __name__ == "__main__":
    asyncio.run(main())
