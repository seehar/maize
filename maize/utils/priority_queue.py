from asyncio import PriorityQueue
from asyncio import TimeoutError
from asyncio import wait_for


class SpiderPriorityQueue(PriorityQueue):
    def __init__(self, maxsize: int = 0):
        super(PriorityQueue, self).__init__(maxsize=maxsize)

    async def get(self):
        fut = super().get()
        try:
            return await wait_for(fut, timeout=0.1)
        except TimeoutError:
            return None
