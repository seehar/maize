import asyncio
import functools
import signal
import time

from maize.utils.logger import logger


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
        def wapper(*args, **kwargs):
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

        return wapper

    return _retry


def retry_asyncio(retry_times: int=3, interval: int=0):
    """
    协程的重试装饰器
    Args:
        retry_times: 重试次数
        interval: 每次重试之间的间隔

    Returns:

    """

    def _retry(func):
        @functools.wraps(func)  # 将函数的原来属性付给新函数
        async def wapper(*args, **kwargs):
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

        return wapper

    return _retry


def func_timeout(timeout: int):
    """
    函数运行时间限制装饰器
    注: 不支持window
    Args:
        timeout: 超时的时间

    Eg:
        @set_timeout(3)
        def test():
            ...

    Returns:

    """

    def wapper(func):
        def handle(
            signum, frame
        ):  # 收到信号 SIGALRM 后的回调函数，第一个参数是信号的数字，第二个参数是the interrupted stack frame.
            raise TimeoutError

        def new_method(*args, **kwargs):
            signal.signal(signal.SIGALRM, handle)  # 设置信号和回调函数
            signal.alarm(timeout)  # 设置 timeout 秒的闹钟
            r = func(*args, **kwargs)
            signal.alarm(0)  # 关闭闹钟
            return r

        return new_method

    return wapper
