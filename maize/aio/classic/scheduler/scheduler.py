"""
Classic 异步请求调度器。

基于 SpiderPriorityQueue 实现请求的优先级排队与出队。
"""

import typing

from maize.utils.priority_queue import SpiderPriorityQueue

if typing.TYPE_CHECKING:
    from maize import Request


class Scheduler:
    """
    请求调度器，管理待处理请求的优先级队列。

    内部使用 SpiderPriorityQueue（min-heap），数值越小优先级越高。
    """

    def __init__(self):
        self.request_queue: SpiderPriorityQueue | None = None

    def __len__(self):
        if self.request_queue is None:
            return 0
        return self.request_queue.qsize()

    def idle(self) -> bool:
        """
        判断调度器是否空闲（队列为空）。

        :return: 队列为空返回 True，否则 False
        """
        return len(self) == 0

    def open(self):
        """
        打开调度器，初始化优先级队列。
        """
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
        """
        将请求放入优先级队列。

        :param request: 待入队的请求对象
        """
        await self.request_queue.put(request)
