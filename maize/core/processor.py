import time
from asyncio import Queue
from typing import TYPE_CHECKING

from maize.core.http.request import Request
from maize.core.items.items import Item
from maize.utils.log_util import get_logger
from maize.utils.project_util import load_class


if TYPE_CHECKING:
    from maize import BasePipeline
    from maize.core.crawler import Crawler


class Processor:
    def __init__(self, crawler: "Crawler"):
        self.crawler: "Crawler" = crawler
        self.logger = get_logger(crawler, self.__class__.__name__)

        item_max_cache_count = self.crawler.settings.getint("ITEM_MAX_CACHE_COUNT")
        self.item_handle_batch_max_size = self.crawler.settings.getint(
            "ITEM_HANDLE_BATCH_MAX_SIZE"
        )
        self.item_handle_interval = self.crawler.settings.getint("ITEM_HANDLE_INTERVAL")

        self.queue = Queue(maxsize=item_max_cache_count)
        self.item_queue = Queue()
        self._last_handle_item_time = 0
        self.item_pipelines: list["BasePipeline"] = []

    async def open(self):
        item_pipeline_path_list = self.crawler.settings.getlist("ITEM_PIPELINES")
        for pipeline_path in item_pipeline_path_list:
            self.logger.info(f"Loading pipeline: {pipeline_path}")
            pipeline_instance = load_class(pipeline_path)(self.crawler.settings)
            await pipeline_instance.open()
            self.item_pipelines.append(pipeline_instance)

    async def process(self):
        while not self.idle():
            result = await self.queue.get()
            if isinstance(result, Request):
                await self.crawler.engine.enqueue_request(result)
            else:
                assert isinstance(result, Item)
                await self._process_item(result)

    async def _process_item(self, item: Item):
        await self.item_queue.put(item)
        current_time = int(time.time())
        if (
            (current_time - self.item_handle_interval) > self._last_handle_item_time
        ) or self.item_queue.full():
            self._last_handle_item_time = current_time
            await self.single_process_item()

    async def single_process_item(self):
        """
        处理单次任务
        @return:
        """
        batch_items = []
        for _ in range(self.item_handle_batch_max_size):
            if self.item_queue.empty():
                break

            batch_items.append(await self.item_queue.get())

        if not batch_items:
            self.logger.debug("no more items to process")
            return

        for pipeline in self.item_pipelines:
            await pipeline.process_item(batch_items)

    async def close(self):
        while not self.item_queue.empty():
            await self.single_process_item()

        for pipeline in self.item_pipelines:
            await pipeline.close()

    async def enqueue(self, output: Request | Item):
        await self.queue.put(output)
        await self.process()

    def idle(self) -> bool:
        return len(self) == 0

    def item_idle(self):
        return self.item_queue.empty()

    def __len__(self):
        return self.queue.qsize()
