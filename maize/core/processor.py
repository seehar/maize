from asyncio import Queue

from maize.core.http.request import Request
from maize.core.items.items import Item


class Processor:
    def __init__(self, crawler):
        self.crawler = crawler
        self.queue = Queue()

    async def process(self):
        while not self.idle():
            result = await self.queue.get()
            if isinstance(result, Request):
                await self.crawler.engine.enqueue_request(result)
            else:
                assert isinstance(result, Item)
                await self._process_item(result)

    async def _process_item(self, item: Item):
        print(item)

    async def enqueue(self, output: Request | Item):
        await self.queue.put(output)
        await self.process()

    def idle(self) -> bool:
        return len(self) == 0

    def __len__(self):
        return self.queue.qsize()
