from inspect import isasyncgen
from inspect import isgenerator
from typing import Any
from typing import AsyncGenerator
from typing import TypeVar

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
