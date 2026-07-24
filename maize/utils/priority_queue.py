"""
异步爬虫优先级队列，基于 asyncio.PriorityQueue，超时返回 None。
"""

from asyncio import PriorityQueue, TimeoutError, wait_for


class SpiderPriorityQueue(PriorityQueue):
    """
    异步优先级队列，按 Request.priority 升序出队（min-heap）。

    :param maxsize: 队列最大容量，0 表示不限，默认 0
    """

    def __init__(self, maxsize: int = 0):
        super().__init__(maxsize=maxsize)

    async def get(self):
        """
        出队一个请求，超时 0.1 秒返回 None。

        :return: 优先级最高的请求，超时返回 None
        """
        fut = super().get()
        try:
            return await wait_for(fut, timeout=0.1)
        except TimeoutError:
            return None

    async def get_by_priority(self, gte_priority: int):
        """
        获取指定优先级的元素

        :param gte_priority: 获取大于等于指定优先级的元素
        :return: 大于等于指定优先级的元素
        """
        item = await self.get()
        if item is None:
            return None

        if item.priority >= gte_priority:
            return item
        await self.put(item)
        return None
