from asyncio import Queue
from typing import TYPE_CHECKING, Union

from maize.common.http.request import Request
from maize.common.items import Item
from maize.middlewares.middleware_manager import PipelineMiddlewareManager
from maize.pipelines.pipeline_scheduler import PipelineScheduler
from maize.utils.log_util import get_logger

if TYPE_CHECKING:
    from maize import BasePipeline
    from maize.core.crawler import Crawler


class Processor:
    def __init__(self, crawler: "Crawler"):
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
        await self.pipeline_middleware_manager.open()
        await self.pipeline_scheduler.open()

    async def process(self):
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
        close_process_result = await self.pipeline_scheduler.close()
        await self.crawler.spider.stats_collector.record_pipeline_success(close_process_result.success_count)
        await self.crawler.spider.stats_collector.record_pipeline_fail(close_process_result.fail_count)
        await self.pipeline_middleware_manager.close()
        self.logger.debug("processor closed")

    async def enqueue(self, output: Union[Request, Item]):
        await self.queue.put(output)
        await self.process()

    def idle(self) -> bool:
        return len(self) == 0
