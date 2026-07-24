"""同步处理器。

与异步版 ``Processor`` 对应，使用 ``queue.Queue`` 替代 ``asyncio.Queue``。
处理 Item（走管道）和 Request（回调度器）。

线程安全：``enqueue``/``process`` 可在 SyncEngine 线程池的多个 worker 中并发调用，
内部用 ``threading.Lock`` 保证管道处理的互斥。
"""

import queue
import threading
from typing import TYPE_CHECKING, Union

from maize.common.http.request import Request
from maize.common.items import Item
from maize.sync.classic.middleware.sync_middleware_manager import SyncPipelineMiddlewareManager
from maize.sync.classic.pipeline.sync_pipeline_scheduler import SyncPipelineScheduler
from maize.utils.log_util import get_logger

if TYPE_CHECKING:
    from maize.sync.classic.crawler.sync_crawler import SyncCrawler


class SyncProcessor:
    """同步处理器，线程安全。"""

    def __init__(self, crawler: "SyncCrawler"):
        """
        初始化同步处理器。

        :param crawler: 当前 SyncCrawler 实例
        """
        self.crawler: SyncCrawler = crawler
        self.logger = get_logger(crawler.settings, self.__class__.__name__)

        self.queue: queue.Queue = queue.Queue()
        self._lock = threading.Lock()
        self.item_pipelines: list = []

        self.pipeline_scheduler: SyncPipelineScheduler = SyncPipelineScheduler(self.crawler.settings)

        self.pipeline_middleware_manager: SyncPipelineMiddlewareManager = SyncPipelineMiddlewareManager(
            self.crawler, self.crawler.settings.middleware.pipeline_middlewares
        )

    def __len__(self):
        return self.queue.qsize()

    def open(self):
        """
        打开管道中间件管理器和管道调度器。
        """
        self.pipeline_middleware_manager.open()
        self.pipeline_scheduler.open()

    def process(self):
        """排空队列中的所有产出，线程安全。"""
        with self._lock:
            while not self.idle():
                result = self.queue.get()
                if isinstance(result, Request):
                    assert self.crawler.engine is not None
                    self.crawler.engine.enqueue_request(result)
                else:
                    assert isinstance(result, Item)

                    assert self.crawler.spider is not None
                    item = self.pipeline_middleware_manager.process_item_before(
                        result,
                        self.crawler.spider,  # type: ignore[arg-type]
                    )

                    if item is None:
                        self.logger.debug("Item was dropped by pipeline middleware")
                        continue

                    process_result = self.pipeline_scheduler.process(item)

                    assert self.crawler.spider is not None
                    self.pipeline_middleware_manager.process_item_after(
                        item,
                        self.crawler.spider,  # type: ignore[arg-type]
                    )

                    if self.crawler.spider and self.crawler.spider.stats_collector:
                        self.crawler.spider.stats_collector.record_pipeline_success(process_result.success_count)
                        self.crawler.spider.stats_collector.record_pipeline_fail(process_result.fail_count)

    def close(self):
        """
        关闭管道调度器并记录最终统计，然后关闭管道中间件管理器。
        """
        close_process_result = self.pipeline_scheduler.close()
        if self.crawler.spider and self.crawler.spider.stats_collector:
            self.crawler.spider.stats_collector.record_pipeline_success(close_process_result.success_count)
            self.crawler.spider.stats_collector.record_pipeline_fail(close_process_result.fail_count)
        self.pipeline_middleware_manager.close()
        self.logger.debug("processor closed")

    def enqueue(self, output: Union[Request, Item]):
        """
        将 Spider 产出（Request 或 Item）入队并立即触发消费。

        :param output: Spider 产出的 Request 或 Item
        """
        self.queue.put(output)
        self.process()

    def idle(self) -> bool:
        """
        检查处理器队列是否为空。

        :return: 队列为空返回 True
        """
        return len(self) == 0
