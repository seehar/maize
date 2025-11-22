import asyncio
import functools
import logging
import time
from threading import RLock


def retry(retry_times: int = 3, interval: int = 0):
    """
    普通函数的重试装饰器
    Args:
        retry_times: 重试次数
        interval: 每次重试之间的间隔

    Returns:

    """

    def _retry(func):
        @functools.wraps(func)  # 将函数的原来属性付给新函数
        def wrapper(*args, **kwargs):
            for i in range(retry_times):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    logging.error(f"函数 {func.__name__} 执行失败 重试 {i + 1} 次. error {e}")
                    time.sleep(interval)
                    if i + 1 >= retry_times:
                        raise e
            return None

        return wrapper

    return _retry


def retry_asyncio(retry_times: int = 3, interval: int = 0):
    """
    协程的重试装饰器
    Args:
        retry_times: 重试次数
        interval: 每次重试之间的间隔

    Returns:

    """

    def _retry(func):
        @functools.wraps(func)  # 将函数的原来属性付给新函数
        async def wrapper(*args, **kwargs):
            for i in range(retry_times):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    logging.error(f"函数 {func.__name__} 执行失败 重试 {i + 1} 次. error {e}")
                    await asyncio.sleep(interval)
                    if i + 1 >= retry_times:
                        raise e
            return None

        return wrapper

    return _retry


class SingletonType(type):
    single_lock = RLock()

    def __call__(cls, *args, **kwargs):
        with SingletonType.single_lock:
            if not hasattr(cls, "_instance"):
                cls._instance = super().__call__(*args, **kwargs)  # 创建cls的对象

        return cls._instance
