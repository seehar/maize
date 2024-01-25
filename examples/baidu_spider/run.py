import asyncio

from examples.baidu_spider.spiders.baidu_spider import BaiduSpider
from maize import CrawlerProcess


async def run():
    process = CrawlerProcess()
    await process.crawl(BaiduSpider)
    await process.start()


if __name__ == "__main__":
    asyncio.run(run())
