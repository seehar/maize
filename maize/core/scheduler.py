import typing

from maize.utils.priority_queue import SpiderPriorityQueue


class Scheduler:
    def __init__(self):
        self.request_queue: typing.Optional[SpiderPriorityQueue] = None

    def open(self):
        self.request_queue = SpiderPriorityQueue()

    async def next_request(self):
        return await self.request_queue.get()

    async def enqueue_request(self, request):
        await self.request_queue.put(request)

    def idle(self) -> bool:
        return len(self) == 0

    def __len__(self):
        return self.request_queue.qsize()
