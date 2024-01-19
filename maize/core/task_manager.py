import asyncio
import typing
from asyncio import Semaphore
from asyncio import Task


class TaskManager:
    def __init__(self, total_concurrency: int = 1):
        self.current_task: typing.Final[set] = set()
        self.semaphore: Semaphore = Semaphore(total_concurrency)

    def create_task(self, coroutine: typing.Awaitable) -> Task:
        task = asyncio.create_task(coroutine)
        self.current_task.add(task)

        def done_callback(_fut: Task[None]) -> None:
            self.current_task.remove(task)
            self.semaphore.release()

        task.add_done_callback(done_callback)
        return task

    def all_done(self) -> bool:
        return len(self.current_task) == 0
