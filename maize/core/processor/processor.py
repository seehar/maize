"""
异步处理器，负责消费 Spider 产出的 Request 和 Item，分发到引擎或管道。
"""

from asyncio import Queue
from typing import TYPE_CHECKING, Union

from maize.common.http.request import Request
from maize.common.items import Item
from maize.middlewares.middleware_manager import PipelineMiddlewareManager
from maize.pipelines.pipeline_scheduler import PipelineScheduler
from maize.utils.log_util import get_logger

if TYPE_CHECKING:
    from maize import BasePipeline
    from maize.aio.classic.crawler.crawler import Crawler


class Processor:
    """
    异步处理器，从内部队列取出 Request/Item 并分发。

    Request 重新入队到引擎调度器，Item 经过管道中间件后交由管道调度器处理。

    :param crawler: 当前 Crawler 实例
    """

    def __init__(self, crawler: "Crawler"):
        """
        初始化处理器。

        :param crawler: 当前 Crawler 实例
        """
        self.crawler: Crawler = crawler
        self.logger = get_logger(crawler.settings, self.__class__.__name__)

        self.queue = Queue()
        self.item_pipelines: list[BasePipeline] = []

        self.pipeline_scheduler: PipelineScheduler = PipelineScheduler(self.crawler.settings)

        # 管道中间件管理器
        self.pipeline_middleware_manager: PipelineMiddlewareManager = PipelineMiddlewareManager(
            self.crawler, self.crawler.settings.middleware.pipeline_middlewares
        )

    def __len__(self):
        return self.queue.qsize()

    async def open(self):
        """
        打开管道中间件管理器和管道调度器。
        """
        await self.pipeline_middleware_manager.open()
        await self.pipeline_scheduler.open()

    async def process(self):
        """
        消费队列中的所有 Request/Item。

        Request 重新入队到引擎调度器，Item 经管道中间件处理后交由管道调度器。
        """
        while not self.idle():
            result = await self.queue.get()
            if isinstance(result, Request):
                await self.crawler.engine.enqueue_request(result)
            else:
                assert isinstance(result, Item)

                # Apply pipeline middleware process_item_before
                item = await self.pipeline_middleware_manager.process_item_before(result, self.crawler.spider)

                # If middleware dropped the item, skip processing
                if item is None:
                    self.logger.debug("Item was dropped by pipeline middleware")
                    continue

                process_result = await self.pipeline_scheduler.process(item)

                # Apply pipeline middleware process_item_after
                await self.pipeline_middleware_manager.process_item_after(item, self.crawler.spider)

                await self.crawler.spider.stats_collector.record_pipeline_success(process_result.success_count)
                await self.crawler.spider.stats_collector.record_pipeline_fail(process_result.fail_count)

    async def close(self):
        """
        关闭管道调度器并记录最终统计，然后关闭管道中间件管理器。
        """
        close_process_result = await self.pipeline_scheduler.close()
        await self.crawler.spider.stats_collector.record_pipeline_success(close_process_result.success_count)
        await self.crawler.spider.stats_collector.record_pipeline_fail(close_process_result.fail_count)
        await self.pipeline_middleware_manager.close()
        self.logger.debug("processor closed")

    async def enqueue(self, output: Union[Request, Item]):
        """
        将 Spider 产出（Request 或 Item）入队并立即触发消费。

        :param output: Spider 产出的 Request 或 Item
        """
        await self.queue.put(output)
        await self.process()

    def idle(self) -> bool:
        """
        检查处理器队列是否为空。

        :return: 队列为空返回 True
        """
        return len(self) == 0
