"""同步标准 Spider 接口。

与异步版 `StandardSpiderInterface` 对应，提供 `create_instance`、`idle` 和同步 `run` 入口。
`run` 直接在当前线程执行，不创建事件循环。
"""

from abc import ABC
from typing import TYPE_CHECKING, Optional

from maize.base.interface.sync_spider_interface import SyncSpiderInterface
from maize.sync.classic.crawler.sync_crawler import SyncCrawlerProcess

if TYPE_CHECKING:
    from maize.settings import SpiderSettings
    from maize.sync.classic.crawler.sync_crawler import SyncCrawler
    from maize.sync.classic.stats.sync_stats_collector import SyncStatsCollector


class SyncStandardSpiderInterface(SyncSpiderInterface, ABC):
    __spider_type__: str
    stats_collector: "SyncStatsCollector | None"
    gte_priority: int | None

    @classmethod
    def create_instance(cls, crawler: "SyncCrawler"):
        instance = cls()
        instance.crawler = crawler
        return instance

    def idle(self) -> bool:
        """判断爬虫是否空闲"""
        return True

    def run(
        self,
        settings: Optional["SpiderSettings"] = None,
        settings_path: str | None = "settings.Settings",
    ) -> None:
        """
        启动同步爬虫（直接在当前线程执行，不创建事件循环）。

        :param settings: 配置文件实例，需要继承 SpiderSettings。优先级高于 settings_path
        :param settings_path: 配置文件路径，需要写到类名，默认：settings.Settings
        """
        process = SyncCrawlerProcess(settings=settings, settings_path=settings_path)
        process.crawl(self)
        process.start()
