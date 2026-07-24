"""同步任务管理器。

使用 ``ThreadPoolExecutor`` + ``threading.Semaphore`` 替代异步版的
``asyncio.Task`` + ``asyncio.Semaphore``，实现同步 Classic 引擎的并发控制。
"""

import logging
import threading
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Any, Final


class SyncTaskManager:
    """同步任务管理器，基于线程池。"""

    def __init__(self, total_concurrency: int = 1, logger: logging.Logger | None = None):
        """
        初始化同步任务管理器。

        :param total_concurrency: 最大并发任务数，默认 1
        :param logger: 日志记录器，默认使用类名 logger
        """
        self.current_task: Final[set] = set()
        self._lock = threading.Lock()
        self.semaphore = threading.Semaphore(total_concurrency)
        self._executor: ThreadPoolExecutor | None = None
        self._total_concurrency = total_concurrency
        self._logger = logger or logging.getLogger(self.__class__.__name__)

    def open(self):
        """
        打开任务管理器，创建线程池。
        """
        self._executor = ThreadPoolExecutor(max_workers=self._total_concurrency)

    def create_task(self, func: Callable[..., Any], *args, **kwargs) -> Future:
        """提交任务到线程池。调用方需已持有 semaphore。"""
        if self._executor is None:
            self.open()

        future = self._executor.submit(func, *args, **kwargs)  # type: ignore[union-attr]

        def done_callback(_fut: Future) -> None:
            exc = _fut.exception()
            if exc is not None:
                self._logger.error(f"Task exception: {exc}")
            with self._lock:
                self.current_task.discard(future)
            self.semaphore.release()

        future.add_done_callback(done_callback)
        with self._lock:
            self.current_task.add(future)
        return future

    def all_done(self) -> bool:
        """
        检查所有任务是否已完成。

        :return: 所有任务完成返回 True
        """
        with self._lock:
            return len(self.current_task) == 0

    def close(self):
        """
        关闭任务管理器，等待线程池所有任务完成后释放资源。
        """
        if self._executor:
            self._executor.shutdown(wait=True)
            self._executor = None
