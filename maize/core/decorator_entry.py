# -*- encoding: utf-8 -*-
"""
@author: seehar
@time: 2024/2/22 10:55
@file: decorator_entry.py.py
@desc: 装饰器启动入口
"""
import asyncio
from typing import TYPE_CHECKING
from typing import Callable
from typing import Optional
from typing import Type

from maize import CrawlerProcess


if TYPE_CHECKING:
    from maize import Spider


class SpiderEntry:
    def __init__(self):
        self.spider_list: list[Type["Spider"]] = []

    def register(
        self, *, settings: Optional[dict] = None
    ) -> Callable[[Type["Spider"]], Type["Spider"]]:
        def wrapper(spider: Type["Spider"]) -> Type["Spider"]:
            if settings:
                if hasattr(spider, "custom_settings"):
                    custom_settings: dict = getattr(spider, "custom_settings")
                    custom_settings.update(settings)
                    setattr(spider, "custom_settings", custom_settings)
                else:
                    setattr(spider, "custom_settings", settings)

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

    def get_spider_list(self) -> list[Type["Spider"]]:
        return self.spider_list
