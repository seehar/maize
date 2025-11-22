import asyncio

from examples.baidu_spider.spiders.baidu_spider import BaiduSpider
from maize import SpiderSettings


async def run():
    spider_settings = SpiderSettings()
    spider_settings.logger_handler = "examples.baidu_spider.logger_util.InterceptHandler"
    spider_settings.request.random_wait_time = (10, 15)

    BaiduSpider().run(spider_settings)


if __name__ == "__main__":
    asyncio.run(run())
