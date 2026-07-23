"""同步处理器。

与异步版 ``Processor`` 对应，使用 ``queue.Queue`` 替代 ``asyncio.Queue``。
处理 Item（走管道）和 Request（回调度器）。
"""

import queue
from typing import TYPE_CHECKING, Union

from maize.common.http.request import Request
from maize.common.items import Item
from maize.sync.classic.middleware.sync_middleware_manager import SyncPipelineMiddlewareManager
from maize.sync.classic.pipeline.sync_pipeline_scheduler import SyncPipelineScheduler
from maize.utils.log_util import get_logger

if TYPE_CHECKING:
    from maize.sync.classic.crawler.sync_crawler import SyncCrawler


class SyncProcessor:
    """同步处理器。"""

    def __init__(self, crawler: "SyncCrawler"):
        self.crawler: SyncCrawler = crawler
        self.logger = get_logger(crawler.settings, self.__class__.__name__)

        self.queue: queue.Queue = queue.Queue()
        self.item_pipelines: list = []

        self.pipeline_scheduler: SyncPipelineScheduler = SyncPipelineScheduler(self.crawler.settings)

        self.pipeline_middleware_manager: SyncPipelineMiddlewareManager = SyncPipelineMiddlewareManager(
            self.crawler, self.crawler.settings.middleware.pipeline_middlewares
        )

    def __len__(self):
        return self.queue.qsize()

    def open(self):
        self.pipeline_middleware_manager.open()
        self.pipeline_scheduler.open()

    def process(self):
        while not self.idle():
            result = self.queue.get()
            if isinstance(result, Request):
                self.crawler.engine.enqueue_request(result)
            else:
                assert isinstance(result, Item)

                item = self.pipeline_middleware_manager.process_item_before(result, self.crawler.spider)

                if item is None:
                    self.logger.debug("Item was dropped by pipeline middleware")
                    continue

                process_result = self.pipeline_scheduler.process(item)

                self.pipeline_middleware_manager.process_item_after(item, self.crawler.spider)

                self.crawler.spider.stats_collector.record_pipeline_success(process_result.success_count)
                self.crawler.spider.stats_collector.record_pipeline_fail(process_result.fail_count)

    def close(self):
        close_process_result = self.pipeline_scheduler.close()
        self.crawler.spider.stats_collector.record_pipeline_success(close_process_result.success_count)
        self.crawler.spider.stats_collector.record_pipeline_fail(close_process_result.fail_count)
        self.pipeline_middleware_manager.close()
        self.logger.debug("processor closed")

    def enqueue(self, output: Union[Request, Item]):
        self.queue.put(output)
        self.process()

    def idle(self) -> bool:
        return len(self) == 0
