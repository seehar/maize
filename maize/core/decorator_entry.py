"""
@author: seehar
@time: 2024/2/22 10:55
@file: decorator_entry.py.py
@desc: 装饰器启动入口
"""

import asyncio
from collections.abc import Callable
from typing import TYPE_CHECKING

from maize import CrawlerProcess

if TYPE_CHECKING:
    from maize import Spider


class SpiderEntry:
    def __init__(self):
        self.spider_list: list[type[Spider]] = []

    def register(self, *, settings: dict | None = None) -> Callable[[type["Spider"]], type["Spider"]]:
        def wrapper(spider: type["Spider"]) -> type["Spider"]:
            if settings:
                if hasattr(spider, "custom_settings"):
                    custom_settings: dict = spider.custom_settings
                    custom_settings.update(settings)
                    spider.custom_settings = custom_settings
                else:
                    spider.custom_settings = settings

            self.spider_list.append(spider)
            return spider

        return wrapper

    async def run_async(self):
        process = CrawlerProcess()
        for spider in self.spider_list:
            await process.crawl(spider)
        await process.start()

    def run(self):
        asyncio.run(self.run_async())

    def get_spider_list(self) -> list[type["Spider"]]:
        return self.spider_list
