from asyncio import PriorityQueue, TimeoutError, wait_for


class SpiderPriorityQueue(PriorityQueue):
    def __init__(self, maxsize: int = 0):
        super().__init__(maxsize=maxsize)

    async def get(self):
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
