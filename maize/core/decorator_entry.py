"""
装饰器启动入口，提供 Spider 注册和批量运行能力。
"""

import asyncio
from collections.abc import Callable
from typing import TYPE_CHECKING

from maize import CrawlerProcess

if TYPE_CHECKING:
    from maize import Spider


class SpiderEntry:
    """
    爬虫装饰器启动入口，用于注册和批量运行多个 Spider。

    使用方式::

        entry = SpiderEntry()

        @entry.register(settings={"CONCURRENCY": 10})
        class MySpider(Spider):
            ...

        entry.run()
    """

    def __init__(self):
        """
        初始化入口，创建空的 Spider 注册列表。
        """
        self.spider_list: list[type[Spider]] = []

    def register(self, *, settings: dict | None = None) -> Callable[[type["Spider"]], type["Spider"]]:
        """
        注册 Spider 的装饰器。

        :param settings: 可选的自定义配置，会合并到 Spider.custom_settings
        :return: 装饰器函数
        """

        def wrapper(spider: type["Spider"]) -> type["Spider"]:
            """
            装饰器内部函数，合并配置并注册 Spider。

            :param spider: 被装饰的 Spider 类
            :return: 原 Spider 类（已注册）
            """
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
        """
        异步运行所有已注册的 Spider。
        """
        process = CrawlerProcess()
        for spider in self.spider_list:
            await process.crawl(spider)
        await process.start()

    def run(self):
        """
        同步运行所有已注册的 Spider（内部调用 asyncio.run）。
        """
        asyncio.run(self.run_async())

    def get_spider_list(self) -> list[type["Spider"]]:
        """
        获取所有已注册的 Spider 类列表。

        :return: Spider 类列表
        """
        return self.spider_list
