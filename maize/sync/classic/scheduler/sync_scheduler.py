"""同步调度器。

与异步版 ``Scheduler`` 对应，使用 ``SyncSpiderPriorityQueue`` 替代 ``asyncio.PriorityQueue``。
"""

import typing

from maize.utils.sync_priority_queue import SyncSpiderPriorityQueue

if typing.TYPE_CHECKING:
    from maize.common.http.request import Request


class SyncScheduler:
    """同步请求调度器。"""

    def __init__(self):
        self.request_queue: SyncSpiderPriorityQueue | None = None

    def __len__(self):
        if self.request_queue is None:
            return 0
        return len(self.request_queue)

    def idle(self) -> bool:
        return len(self) == 0

    def open(self):
        self.request_queue = SyncSpiderPriorityQueue()

    def next_request(self, gte_priority: int | None = None):
        """
        获取下一个请求。

        :param gte_priority: 大于等于优先级，为 None 时不指定优先级
        :return: Request 或 None
        """
        if gte_priority is None:
            return self.request_queue.get()

        return self.request_queue.get_by_priority(gte_priority)

    def enqueue_request(self, request: "Request"):
        self.request_queue.put(request)
