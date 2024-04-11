import typing

from maize.utils.priority_queue import SpiderPriorityQueue


if typing.TYPE_CHECKING:
    from maize import Request


class Scheduler:
    def __init__(self):
        self.request_queue: typing.Optional[SpiderPriorityQueue] = None

    def __len__(self):
        return self.request_queue.qsize()

    def idle(self) -> bool:
        return len(self) == 0

    def open(self):
        self.request_queue = SpiderPriorityQueue()

    async def next_request(self):
        return await self.request_queue.get()

    async def enqueue_request(self, request: "Request"):
        await self.request_queue.put(request)
