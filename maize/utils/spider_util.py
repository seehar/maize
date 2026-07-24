"""
Spider 工具，提供回调返回值的生成器转换。
"""

from collections.abc import AsyncGenerator, Generator
from inspect import isasyncgen, isgenerator
from typing import Any, TypeVar

from maize.exceptions.spider_exception import TransformTypeException

T = TypeVar("T")


async def transform(func_result: T) -> AsyncGenerator[T, Any]:
    """
    将回调返回值转换为异步生成器。

    :param func_result: 回调返回值，必须是 generator 或 async generator
    :return: 异步生成器
    :raises TransformTypeException: 返回值不是 generator 或 async generator
    """
    if isgenerator(func_result):
        for r in func_result:
            yield r
    elif isasyncgen(func_result):
        async for r in func_result:
            yield r
    else:
        raise TransformTypeException("callback return value must be `generator` or `async generator`")


def transform_sync(func_result: T) -> Generator[T, Any, None]:
    """同步版本的 transform，用于同步爬虫。callback 返回值必须是 generator。"""
    if isgenerator(func_result):
        yield from func_result
    else:
        raise TransformTypeException("sync callback return value must be `generator`")
