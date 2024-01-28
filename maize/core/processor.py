from asyncio import Queue
from typing import TYPE_CHECKING

from maize.core.http.request import Request
from maize.core.items.items import Item
from maize.core.pipelines.pipeline_scheduler import PipelineScheduler
from maize.utils.log_util import get_logger


if TYPE_CHECKING:
    from maize import BasePipeline
    from maize.core.crawler import Crawler


class Processor:
    def __init__(self, crawler: "Crawler"):
        self.crawler: "Crawler" = crawler
        self.logger = get_logger(crawler.settings, self.__class__.__name__)

        self.queue = Queue()
        self.item_pipelines: list["BasePipeline"] = []

        self.pipeline_scheduler: PipelineScheduler = PipelineScheduler(
            self.crawler.settings
        )

    async def open(self):
        await self.pipeline_scheduler.open()

    async def process(self):
        while not self.idle():
            result = await self.queue.get()
            if isinstance(result, Request):
                await self.crawler.engine.enqueue_request(result)
            else:
                assert isinstance(result, Item)
                await self.pipeline_scheduler.process(result)

    async def close(self):
        await self.pipeline_scheduler.close()
        self.logger.debug("processor closed")

    async def enqueue(self, output: Request | Item):
        await self.queue.put(output)
        await self.process()

    def idle(self) -> bool:
        return len(self) == 0

    def __len__(self):
        return self.queue.qsize()
