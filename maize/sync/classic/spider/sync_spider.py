"""同步 Classic 爬虫 Spider 基类。

与异步版 ``Spider`` 对应，``start_requests``/``parse``/``open``/``close`` 均为同步。
``start_requests`` 返回普通 ``Generator``（yield Request），``parse`` 可返回生成器或 None。
"""

import threading
from abc import abstractmethod
from collections.abc import Generator
from typing import TYPE_CHECKING, Any

from maize.base.interface.sync_standard_spider_interface import SyncStandardSpiderInterface
from maize.common.http import Response
from maize.common.http.request import Request
from maize.sync.classic.stats.sync_stats_collector import SyncStatsCollector
from maize.utils.log_util import get_logger

if TYPE_CHECKING:
    from logging import Logger

    from maize.sync.classic.crawler.sync_crawler import SyncCrawler


class SyncSpider(SyncStandardSpiderInterface):
    """同步 Classic 爬虫基类。"""

    __spider_type__: str = "spider"

    def __init__(self):
        super().__init__()
        self._lock = threading.Lock()

        self.crawler: SyncCrawler | None = None
        self.stats_collector: SyncStatsCollector | None = None
        self.logger: Logger | None = None

        self.gte_priority: int | None = None

    def open(self):
        """在 Spider 启动时执行初始化操作。"""
        self.logger = get_logger()

        self.stats_collector = SyncStatsCollector(self.__class__.__name__)
        self.stats_collector.open()

    def close(self):
        """在 Spider 关闭时执行清理操作。"""
        if self.stats_collector:
            self.stats_collector.close()

    @abstractmethod
    def start_requests(self) -> Generator[Request, Any, None]:
        raise NotImplementedError

    def parse(self, response: Response):
        """
        自定义解析方法。

        子类可重写为生成器（yield Request / Item）或普通方法（return None）。
        """
        raise NotImplementedError

    def pause_spider(self, lte_priority: int | None = None):
        """暂停爬虫。"""
        with self._lock:
            if self.gte_priority is not None:
                self.logger.warning("爬虫已暂停，请勿重复暂停")
                return
            if lte_priority is None:
                lte_priority = 0
            self.gte_priority = lte_priority + 1

    def proceed_spider(self, gte_priority: int | None = None):
        """继续爬虫。"""
        with self._lock:
            if gte_priority is None:
                self.gte_priority = None
                return
            self.gte_priority = gte_priority

    def idle(self) -> bool:
        return self.stats_collector.idle() if self.stats_collector else True

    def is_pause(self):
        """判断爬虫是否暂停。"""
        return self.gte_priority is not None
