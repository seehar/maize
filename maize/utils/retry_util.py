import asyncio
import functools
import logging
import time
from collections.abc import Callable
from typing import Concatenate
from typing import ParamSpec
from typing import TypeVar

from ..exceptions import MaxRetryException
from ..exceptions import RetryNotCatchException


# from .logger_util import logger


P = ParamSpec("P")
R = TypeVar("R")
logging.getLogger("maize")
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def retry(func: Callable[P, R]) -> Callable[Concatenate[P], R]:
    """
    重试装饰器，只能用在 class 方法上
    必须有以下三个属性
        retry_max_count: int
        retry_max_timeout: int = 1
        retry_catch_exc: Type[BaseException] = Exception
        retry_not_catch_exc: Type[BaseException] = ()

    :param func:
    :return:
    """

    @functools.wraps(func)
    def sync_wrapper(*args: P.args, **kwargs: P.kwargs):
        retry_count = 0
        last_exception = None
        retry_max_count = args[0].retry_max_count
        while retry_count < retry_max_count:
            try:
                return func(*args, **kwargs)
            except args[0].retry_not_catch_exc as e:
                raise RetryNotCatchException(f"重试时不需要捕获的异常，异常信息：{e}")
            except args[0].retry_catch_exc as e:
                last_exception = e
                logging.warning(f"重试中({retry_count + 1}/{retry_max_count})，异常信息：{e}")
                retry_count += 1
                time.sleep(args[0].retry_max_timeout)
        raise MaxRetryException(
            f"超过最大重试次数({retry_max_count})。最后一次异常信息：{last_exception}"
        )

    @functools.wraps(func)
    async def async_wrapper(*args: P.args, **kwargs: P.kwargs):
        retry_count = 0
        last_exception = None
        retry_max_count = args[0].retry_max_count
        while retry_count < retry_max_count:
            try:
                return await func(*args, **kwargs)
            except args[0].retry_catch_exc as e:
                last_exception = e
                logging.warning(f"重试中({retry_count + 1}/{retry_max_count})，异常信息：{e}")
                retry_count += 1
                time.sleep(args[0].retry_max_timeout)
        raise MaxRetryException(
            f"超过最大重试次数({retry_max_count})。最后一次异常信息：{last_exception}"
        )

    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
