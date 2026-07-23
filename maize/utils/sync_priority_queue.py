"""同步爬虫优先级队列。

基于 `queue.PriorityQueue` 实现，用于同步 Classic 引擎的请求调度。
与异步版 `SpiderPriorityQueue` 对应：min-heap，priority 数值越小越优先出队。
"""

import queue
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from maize.common.http.request import Request


class SyncSpiderPriorityQueue:
    """同步优先级队列，按 Request.priority 升序出队。"""

    def __init__(self, maxsize: int = 0):
        self._queue: queue.PriorityQueue[tuple[int, int, Request]] = queue.PriorityQueue(maxsize=maxsize)
        self._tie_breaker: int = 0

    def qsize(self) -> int:
        return self._queue.qsize()

    def __len__(self) -> int:
        return self._queue.qsize()

    def empty(self) -> bool:
        return self._queue.empty()

    def put(self, request: "Request") -> None:
        """入队，按 priority 排序；tie_breaker 保证同 priority 时 FIFO，避免 Request 比较报错。"""
        self._tie_breaker += 1
        self._queue.put((request.priority, self._tie_breaker, request))

    def get(self, timeout: float | None = 0.1) -> "Request | None":
        """出队，超时返回 None（模仿异步版 0.1s timeout 语义）。"""
        try:
            _priority, _seq, request = self._queue.get(timeout=timeout)
            return request
        except queue.Empty:
            return None

    def get_by_priority(self, gte_priority: int, timeout: float | None = 0.1) -> "Request | None":
        """获取大于等于指定优先级的元素，不满足则放回。"""
        request = self.get(timeout=timeout)
        if request is None:
            return None
        if request.priority >= gte_priority:
            return request
        self.put(request)
        return None

    def task_done(self) -> None:
        self._queue.task_done()
