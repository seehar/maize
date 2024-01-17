import asyncio
import typing
from asyncio import Future
from asyncio import Semaphore
from asyncio import Task


class TaskManager:
    def __init__(self, total_concurrency: int = 1):
        print(f"当前并发数: {total_concurrency}")
        self.current_task: typing.Final[set] = set()
        self.semaphore: Semaphore = Semaphore(total_concurrency)

    def create_task(self, coroutine) -> Task:
        task = asyncio.create_task(coroutine)
        self.current_task.add(task)

        def done_callback(_fut: Future) -> None:
            self.current_task.remove(task)
            self.semaphore.release()

        task.add_done_callback(done_callback)
        return task

    def all_done(self) -> bool:
        # return bool(self.current_task)
        return len(self.current_task) == 0
