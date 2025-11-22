import asyncio
import typing
from abc import ABCMeta, abstractmethod
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Any

from maize.common.http import Response
from maize.common.http.request import Request
from maize.core.crawler import CrawlerProcess
from maize.core.stats_collector import StatsCollector
from maize.settings import SpiderSettings
from maize.utils.log_util import get_logger

if TYPE_CHECKING:
    from logging import Logger

    from maize.core.crawler import Crawler


class Spider(metaclass=ABCMeta):
    def __init__(self):
        self._lock = asyncio.Lock()
        self.__spider_type__: str = "spider"

        self.crawler: Crawler | None = None
        self.stats_collector: StatsCollector | None = None
        self.logger: Logger | None = None

        self.gte_priority: int | None = None

    def __str__(self):
        return self.__class__.__name__

    async def open(self, settings: "SpiderSettings"):
        """
        在 Spider 启动时执行一些初始化操作

        :param settings: 处理后的爬虫配置。将自定义的配置与默认配置合并
        :return:
        """
        self.logger = get_logger(settings, self.__class__.__name__)

        self.stats_collector = StatsCollector(settings, self.__class__.__name__)
        await self.stats_collector.open()

    async def close(self):
        """
        在 Spider 关闭时执行一些清理操作

        :return:
        """
        await self.stats_collector.close()

    @classmethod
    def create_instance(cls, crawler: "Crawler"):
        instance = cls()
        instance.crawler = crawler
        return instance

    @abstractmethod
    async def start_requests(self) -> AsyncGenerator[Request, Any]:
        raise NotImplementedError

    async def parse(self, response: Response):
        """
        自定义解析方法

        :param response: 封装后的响应实例
        :return:
        """
        raise NotImplementedError

    async def pause_spider(self, lte_priority: int | None = None):
        """
        暂停爬虫

        :param lte_priority: 请求优先级，默认为 None。为 None 时暂停采集所有的请求，否则只暂停采集小于 priority 的请求
        :return:
        """
        async with self._lock:
            if self.gte_priority is not None:
                self.logger.warning("爬虫已暂停，请勿重复暂停")
                return

            if lte_priority is None:
                self.gte_priority = 0
                return

            self.gte_priority = lte_priority + 1

    async def proceed_spider(self, gte_priority: int | None = None):
        """
        继续爬虫

        :param gte_priority: 请求优先级，默认为 None。为 None 时继续采集所有的请求，否则只继续采集大于等于 priority 的请求
        :return:
        """
        async with self._lock:
            if gte_priority is None:
                self.gte_priority = None
                return

            self.gte_priority = gte_priority

    def idle(self) -> bool:
        return self.stats_collector.idle() and not self.is_pause()

    def is_pause(self):
        """
        爬虫是否暂停

        :return: 暂停 True，否则 False
        """
        return self.gte_priority is not None

    async def _async_run(
        self,
        settings: typing.Optional["SpiderSettings"] = None,
        settings_path: str | None = "settings.Settings",
    ):
        process = CrawlerProcess(settings=settings, settings_path=settings_path)
        await process.crawl(self)
        await process.start()

    def run(
        self,
        settings: typing.Optional["SpiderSettings"] = None,
        settings_path: str | None = "settings.Settings",
    ):
        """
        启动爬虫

        @param settings: 配置文件实例，需要继承 SpiderSettings，也就是需要传入一个 SpiderSettings 实例。优先级高于 settings_path
        @param settings_path: 配置文件路径，需要写到类名，默认：settings.Settings
        @return:
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self._async_run(settings=settings, settings_path=settings_path))
