import asyncio
import functools
import time

from maize.utils.logger_util import logger


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
                    logger.error(
                        "函数 {} 执行失败 重试 {} 次. error {}".format(func.__name__, i + 1, e)
                    )
                    time.sleep(interval)
                    if i + 1 >= retry_times:
                        raise e

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
                    logger.error(
                        "函数 {} 执行失败 重试 {} 次. error {}".format(func.__name__, i + 1, e)
                    )
                    await asyncio.sleep(interval)
                    if i + 1 >= retry_times:
                        raise e

        return wrapper

    return _retry
