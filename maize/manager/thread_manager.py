import sys
from concurrent.futures import Future
from concurrent.futures import ThreadPoolExecutor
from threading import RLock
from typing import Callable
from typing import List


class ThreadManager:
    def __init__(self, max_workers: int = 2, thread_name_prefix: str = "ThreadManager"):
        """
        初始化线程管理器。

        :param max_workers: 线程池中最大工作线程数。
        :param thread_name_prefix: 线程名称的前缀。
        """
        self._executor = ThreadPoolExecutor(
            max_workers=max_workers, thread_name_prefix=thread_name_prefix
        )
        self._futures: List[Future] = []
        self._lock = RLock()
        self._max_workers = max_workers

    def submit(self, task: Callable, /, *args, **kwargs) -> Future:
        """
        提交一个任务到线程池执行。

        :param task: 要执行的任务，必须是一个可调用对象。
        :param args: 传递给任务的位置参数。
        :param kwargs: 传递给任务的关键字参数。
        :return: 表示任务的 Future 对象。
        """
        future = self._executor.submit(task, *args, **kwargs)

        def done_callback(fut: Future) -> None:
            self._remove_future(fut)

        future.add_done_callback(done_callback)
        with self._lock:
            self._futures.append(future)
        return future

    def shutdown(self, wait: bool = True, cancel_futures: bool = False):
        """
        关闭线程池。

        :param wait: 如果为 True，则等待所有任务完成后再关闭线程池。
        :param cancel_futures: 如果为 True，则取消所有未完成的任务。
        """
        if sys.version_info >= (3, 9):
            self._executor.shutdown(wait=wait, cancel_futures=cancel_futures)
        else:
            self._executor.shutdown(wait=wait)
            if cancel_futures:
                self.__cancel_all_future()

        with self._lock:
            self._futures.clear()

    def __cancel_all_future(self):
        """
        取消所有未完成的任务

        :return:
        """
        with self._lock:
            for future in self._futures:
                future.cancel()

    def all_done(self) -> bool:
        """
        检查所有任务是否已完成。

        :return: 如果所有任务已完成，返回 True；否则返回 False。
        """
        with self._lock:
            return not bool(self._futures)

    def set_max_workers(self, max_workers: int):
        """
        动态设置线程池的最大工作线程数。

        :param max_workers: 新的最大工作线程数。
        """
        if max_workers <= 0:
            raise ValueError("max_workers must be greater than 0")
        self._max_workers = max_workers
        self._executor._max_workers = max_workers
        self._executor._adjust_thread_count()

    def _remove_future(self, future: Future) -> None:
        """
        从 futures 列表中移除指定的 Future 对象。

        :param future: 要移除的 Future 对象。
        """
        with self._lock:
            if future in self._futures:
                self._futures.remove(future)
