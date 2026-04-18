"""
Tests for spider_util
"""

import pytest

from maize.utils.spider_util import transform


class TestSpiderUtil:
    """Test spider_util"""

    @pytest.mark.asyncio
    async def test_transform_with_async_generator(self):
        """Test transform with async generator"""

        async def async_gen():
            yield 1
            yield 2
            yield 3

        results = []
        async for item in transform(async_gen()):
            results.append(item)

        assert results == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_transform_with_multiple_async_generator(self):
        """Test transform with async generator yielding multiple values"""

        async def async_gen():
            yield "hello"
            yield "world"

        results = []
        async for item in transform(async_gen()):
            results.append(item)

        assert results == ["hello", "world"]
