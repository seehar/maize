import asyncio
from abc import ABC
from typing import TYPE_CHECKING, Optional

from maize.aio.classic.crawler.crawler import CrawlerProcess
from maize.base.interface.spider_interface import SpiderInterface

if TYPE_CHECKING:
    from maize.aio.classic.crawler.crawler import Crawler
    from maize.core.stats.stats_collector import StatsCollector
    from maize.settings import SpiderSettings


class StandardSpiderInterface(SpiderInterface, ABC):
    __spider_type__: str
    stats_collector: Optional["StatsCollector"]
    gte_priority: int | None

    @classmethod
    def create_instance(cls, crawler: "Crawler"):
        instance = cls()
        instance.crawler = crawler
        return instance

    def idle(self) -> bool:
        """
        判断爬虫是否空闲

        :return: 如果爬虫没有待处理的请求或任务，返回 True，否则返回 False
        """
        return True

    async def _async_run(
        self,
        settings: Optional["SpiderSettings"] = None,
        settings_path: str | None = "settings.Settings",
    ):
        process = CrawlerProcess(settings=settings, settings_path=settings_path)
        await process.crawl(self)
        await process.start()

    def run(
        self,
        settings: Optional["SpiderSettings"] = None,
        settings_path: str | None = "settings.Settings",
    ):
        """
        启动爬虫

        :param settings: 配置文件实例，需要继承 SpiderSettings，也就是需要传入一个 SpiderSettings 实例。优先级高于 settings_path
        :param settings_path: 配置文件路径，需要写到类名，默认：settings.Settings
        :return:
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self._async_run(settings=settings, settings_path=settings_path))
