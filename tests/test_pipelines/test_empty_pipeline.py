"""
Tests for EmptyPipeline.
"""

import pytest

from maize.common.items import Item
from maize.pipelines.empty_pipeline import EmptyPipeline
from maize.settings import SpiderSettings


class TestEmptyPipeline:
    """Test EmptyPipeline lifecycle and methods."""

    @pytest.fixture
    def pipeline(self):
        return EmptyPipeline(SpiderSettings())

    @pytest.mark.asyncio
    async def test_open_is_noop(self, pipeline):
        await pipeline.open()

    @pytest.mark.asyncio
    async def test_close_is_noop(self, pipeline):
        await pipeline.close()

    @pytest.mark.asyncio
    async def test_process_item_returns_true(self, pipeline):
        result = await pipeline.process_item([Item()])
        assert result is True

    @pytest.mark.asyncio
    async def test_process_item_empty_list_returns_true(self, pipeline):
        result = await pipeline.process_item([])
        assert result is True

    @pytest.mark.asyncio
    async def test_process_error_item_is_noop(self, pipeline):
        await pipeline.process_error_item([Item()])

    @pytest.mark.asyncio
    async def test_process_error_item_empty_list(self, pipeline):
        await pipeline.process_error_item([])

    @pytest.mark.asyncio
    async def test_full_lifecycle(self, pipeline):
        """open -> process -> close should all succeed."""
        await pipeline.open()
        assert await pipeline.process_item([Item()]) is True
        await pipeline.process_error_item([Item()])
        await pipeline.close()
