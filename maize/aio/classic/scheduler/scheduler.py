import typing

from maize.utils.priority_queue import SpiderPriorityQueue

if typing.TYPE_CHECKING:
    from maize import Request


class Scheduler:
    def __init__(self):
        self.request_queue: SpiderPriorityQueue | None = None

    def __len__(self):
        return self.request_queue.qsize()

    def idle(self) -> bool:
        return len(self) == 0

    def open(self):
        self.request_queue = SpiderPriorityQueue()

    async def next_request(self, gte_priority: int | None = None):
        """
        获取下一个请求

        :param gte_priority: 大于等于优先级，为 None 时不指定优先级
        :return:
        """
        if gte_priority is None:
            return await self.request_queue.get()

        return await self.request_queue.get_by_priority(gte_priority)

    async def enqueue_request(self, request: "Request"):
        await self.request_queue.put(request)
