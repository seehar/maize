"""
Tests for PagePool wait-for-available-page path (lines 41-43).
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from maize.common.downloader.page_pool import PagePool
from maize.settings import SpiderSettings


def _make_crawler():
    crawler = MagicMock()
    crawler.settings = SpiderSettings()
    return crawler


def _make_mock_page():
    page = MagicMock()
    page.is_closed.return_value = False
    page.close = AsyncMock()
    page.remove_listener = MagicMock()
    return page


class TestPagePoolWaitForAvailable:
    """Test PagePool.acquire_page when max_pages reached and must wait."""

    @pytest.mark.asyncio
    async def test_acquire_waits_then_gets_released_page(self):
        """When all pages are in use, acquire waits until one is released."""
        crawler = _make_crawler()
        pool = PagePool(crawler, max_pages=1)

        page1 = _make_mock_page()
        context = MagicMock()
        context.new_page = AsyncMock(return_value=page1)

        # Acquire the only page
        acquired1 = await pool.acquire_page(context)
        assert acquired1 is page1
        assert len(pool.in_use_pages) == 1

        # Start a task to acquire another page (will block)
        async def acquire_second():
            return await pool.acquire_page(context)

        task = asyncio.create_task(acquire_second())

        # Give it a moment to start waiting
        await asyncio.sleep(0.15)

        # Release the first page
        await pool.release_page(page1)

        # The second acquire should now complete
        acquired2 = await asyncio.wait_for(task, timeout=1.0)
        assert acquired2 is page1  # same page was returned to pool

    @pytest.mark.asyncio
    async def test_acquire_creates_new_when_under_limit(self):
        """When below max_pages, a new page is created."""
        crawler = _make_crawler()
        pool = PagePool(crawler, max_pages=5)

        page = _make_mock_page()
        context = MagicMock()
        context.new_page = AsyncMock(return_value=page)

        result = await pool.acquire_page(context)
        assert result is page
        context.new_page.assert_called_once()
