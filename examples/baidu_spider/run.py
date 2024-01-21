import asyncio

from examples.baidu_spider.spiders.baidu_spider import BaiduSpider
from maize import CrawlerProcess
from maize.utils import get_settings


async def run():
    settings = get_settings()
    process = CrawlerProcess(settings)
    await process.crawl(BaiduSpider)
    await process.start()


if __name__ == "__main__":
    asyncio.run(run())
