from asyncio import Queue
from typing import TYPE_CHECKING

from maize.core.http.request import Request
from maize.core.items.items import Item
from maize.utils.log_util import get_logger


if TYPE_CHECKING:
    from maize.core.crawler import Crawler


class Processor:
    def __init__(self, crawler: "Crawler"):
        self.crawler: "Crawler" = crawler
        self.queue = Queue()
        self.logger = get_logger(crawler, self.__class__.__name__)

    async def process(self):
        while not self.idle():
            result = await self.queue.get()
            if isinstance(result, Request):
                await self.crawler.engine.enqueue_request(result)
            else:
                assert isinstance(result, Item)
                await self._process_item(result)

    async def _process_item(self, item: Item):
        self.logger.info(f"process item: {item}")

    async def enqueue(self, output: Request | Item):
        await self.queue.put(output)
        await self.process()

    def idle(self) -> bool:
        return len(self) == 0

    def __len__(self):
        return self.queue.qsize()
