from collections.abc import AsyncGenerator, Generator
from inspect import isasyncgen, isgenerator
from typing import Any, TypeVar

from maize.exceptions.spider_exception import TransformTypeException

T = TypeVar("T")


async def transform(func_result: T) -> AsyncGenerator[T, Any]:
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
