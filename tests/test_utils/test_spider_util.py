"""
Tests for spider_util transform().
"""

import pytest

from maize.exceptions.spider_exception import TransformTypeException
from maize.utils.spider_util import transform


class TestTransformWithSyncGenerator:
    """transform() should forward items from a synchronous generator."""

    @pytest.mark.asyncio
    async def test_sync_generator_forwarded(self):
        def sync_gen():
            yield 1
            yield 2
            yield 3

        results = []
        async for item in transform(sync_gen()):
            results.append(item)

        assert results == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_sync_generator_strings(self):
        def sync_gen():
            yield "hello"
            yield "world"

        results = []
        async for item in transform(sync_gen()):
            results.append(item)

        assert results == ["hello", "world"]

    @pytest.mark.asyncio
    async def test_empty_sync_generator(self):
        def sync_gen():
            return
            yield  # never reached, makes this a generator

        results = []
        async for item in transform(sync_gen()):
            results.append(item)

        assert results == []


class TestTransformWithAsyncGenerator:
    """transform() should forward items from an async generator."""

    @pytest.mark.asyncio
    async def test_async_generator_forwarded(self):
        async def async_gen():
            yield 1
            yield 2
            yield 3

        results = []
        async for item in transform(async_gen()):
            results.append(item)

        assert results == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_async_generator_multiple_values(self):
        async def async_gen():
            yield "hello"
            yield "world"

        results = []
        async for item in transform(async_gen()):
            results.append(item)

        assert results == ["hello", "world"]

    @pytest.mark.asyncio
    async def test_empty_async_generator(self):
        async def async_gen():
            if False:
                yield  # makes this an async generator, but never executes

        results = []
        async for item in transform(async_gen()):
            results.append(item)

        assert results == []

    @pytest.mark.asyncio
    async def test_plain_value_raises(self):
        with pytest.raises(TransformTypeException):
            async for _ in transform(42):
                pass

    @pytest.mark.asyncio
    async def test_string_raises(self):
        with pytest.raises(TransformTypeException):
            async for _ in transform("not a generator"):
                pass

    @pytest.mark.asyncio
    async def test_list_raises(self):
        with pytest.raises(TransformTypeException):
            async for _ in transform([1, 2, 3]):
                pass

    @pytest.mark.asyncio
    async def test_none_raises(self):
        with pytest.raises(TransformTypeException):
            async for _ in transform(None):
                pass
