import asyncio
from asyncio import Semaphore, Task
from collections.abc import Coroutine, Generator
from typing import Any, Final


class TaskManager:
    """
    异步任务管理器，基于 Semaphore 控制并发任务数量。

    :param total_concurrency: 最大并发任务数，默认 1
    """

    def __init__(self, total_concurrency: int = 1):
        """
        初始化任务管理器。

        :param total_concurrency: 最大并发任务数，默认 1
        """
        self.current_task: Final[set] = set()
        self.semaphore: Semaphore = Semaphore(total_concurrency)

    def create_task(self, coroutine: Generator[Any, None, None] | Coroutine[Any, Any, None]) -> Task:
        """
        创建异步任务并加入管理。

        :param coroutine: 协程或生成器
        :return: 创建的 Task 对象
        """
        task = asyncio.create_task(coroutine)
        self.current_task.add(task)

        def done_callback(_fut: Task[None]) -> None:
            self.current_task.remove(task)
            self.semaphore.release()

        task.add_done_callback(done_callback)
        return task

    def all_done(self) -> bool:
        """
        检查所有任务是否已完成。

        :return: 所有任务完成返回 True
        """
        return len(self.current_task) == 0
