from asyncio import Queue
from typing import TYPE_CHECKING
from typing import List
from typing import Union

from maize.common.http.request import Request
from maize.common.items import Item
from maize.pipelines.pipeline_scheduler import PipelineScheduler
from maize.utils.log_util import get_logger


if TYPE_CHECKING:
    from maize import BasePipeline
    from maize.core.crawler import Crawler


class Processor:
    def __init__(self, crawler: "Crawler"):
        self.crawler: "Crawler" = crawler
        self.logger = get_logger(crawler.settings, self.__class__.__name__)

        self.queue = Queue()
        self.item_pipelines: List["BasePipeline"] = []

        self.pipeline_scheduler: PipelineScheduler = PipelineScheduler(self.crawler.settings)

    def __len__(self):
        return self.queue.qsize()

    async def open(self):
        await self.pipeline_scheduler.open()

    async def process(self):
        while not self.idle():
            result = await self.queue.get()
            if isinstance(result, Request):
                await self.crawler.engine.enqueue_request(result)
            else:
                assert isinstance(result, Item)
                process_result = await self.pipeline_scheduler.process(result)
                await self.crawler.spider.stats_collector.record_pipeline_success(process_result.success_count)
                await self.crawler.spider.stats_collector.record_pipeline_fail(process_result.fail_count)

    async def close(self):
        close_process_result = await self.pipeline_scheduler.close()
        await self.crawler.spider.stats_collector.record_pipeline_success(close_process_result.success_count)
        await self.crawler.spider.stats_collector.record_pipeline_fail(close_process_result.fail_count)
        self.logger.debug("processor closed")

    async def enqueue(self, output: Union[Request, Item]):
        await self.queue.put(output)
        await self.process()

    def idle(self) -> bool:
        return len(self) == 0
