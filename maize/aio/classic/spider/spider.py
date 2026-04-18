import asyncio
from abc import abstractmethod
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Any

from maize.base.interface.standard_spider_interface import StandardSpiderInterface
from maize.common.http import Response
from maize.common.http.request import Request
from maize.core.stats.stats_collector import StatsCollector
from maize.utils.log_util import get_logger

if TYPE_CHECKING:
    from logging import Logger

    from maize.aio.classic.crawler.crawler import Crawler


class Spider(StandardSpiderInterface):
    def __init__(self):
        super().__init__()
        self._lock = asyncio.Lock()
        self.__spider_type__: str = "spider"

        self.crawler: Crawler | None = None
        self.stats_collector: StatsCollector | None = None
        self.logger: Logger | None = None

        self.gte_priority: int | None = None

    async def open(self):
        """
        在 Spider 启动时执行一些初始化操作

        :return:
        """
        self.logger = get_logger()

        self.stats_collector = StatsCollector(self.__class__.__name__)
        await self.stats_collector.open()

    async def close(self):
        """
        在 Spider 关闭时执行一些清理操作

        :return:
        """
        await self.stats_collector.close()

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
