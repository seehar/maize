"""
异步标准 Spider 接口。

在 SpiderInterface 基础上增加 create_instance 工厂方法、idle 状态判断
和 run 启动入口（内部创建事件循环）。

同步版对应接口：``maize.base.interface.sync_standard_spider_interface.SyncStandardSpiderInterface``
"""

import asyncio
from abc import ABC
from typing import TYPE_CHECKING, Optional

from maize.aio.classic.crawler.crawler import CrawlerProcess
from maize.base.interface._shared import _StandardSpiderMixin
from maize.base.interface.spider_interface import SpiderInterface

if TYPE_CHECKING:
    from maize.core.stats.stats_collector import StatsCollector
    from maize.settings import SpiderSettings


class StandardSpiderInterface(SpiderInterface, _StandardSpiderMixin, ABC):
    """
    异步标准 Spider 接口。

    提供 create_instance 工厂方法绑定 Crawler、idle 空闲判断、
    以及 run() 同步入口（内部通过 asyncio 事件循环驱动）。
    """

    stats_collector: Optional["StatsCollector"]
    gte_priority: int | None

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
