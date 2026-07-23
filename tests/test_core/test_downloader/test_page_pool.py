"""
Tests for PagePool.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from maize.common.downloader.page_pool import PagePool
from maize.settings import SpiderSettings


def _make_crawler(max_pages=10):
    crawler = MagicMock()
    crawler.settings = SpiderSettings()
    return crawler


def _make_mock_page(is_closed=False):
    page = MagicMock()
    page.is_closed.return_value = is_closed
    page.close = AsyncMock()
    page.remove_listener = MagicMock()
    return page


def _make_mock_context(page=None):
    context = MagicMock()
    context.new_page = AsyncMock(return_value=page or _make_mock_page())
    return context


class TestPagePoolInit:
    def test_init_defaults(self):
        crawler = _make_crawler()
        pool = PagePool(crawler, max_pages=5)
        assert pool.max_pages == 5
        assert pool.available_pages == []
        assert pool.in_use_pages == set()

    def test_logger_set(self):
        crawler = _make_crawler()
        pool = PagePool(crawler)
        assert pool.logger is not None


class TestPagePoolAcquire:
    @pytest.mark.asyncio
    async def test_acquire_creates_new_page_when_under_limit(self):
        crawler = _make_crawler()
        pool = PagePool(crawler, max_pages=5)
        page = _make_mock_page()
        context = _make_mock_context(page)

        result = await pool.acquire_page(context)
        assert result is page
        assert page in pool.in_use_pages
        context.new_page.assert_called_once()

    @pytest.mark.asyncio
    async def test_acquire_reuses_available_page(self):
        crawler = _make_crawler()
        pool = PagePool(crawler, max_pages=5)
        page = _make_mock_page(is_closed=False)
        pool.available_pages.append(page)
        context = _make_mock_context(page)

        result = await pool.acquire_page(context)
        assert result is page
        assert page in pool.in_use_pages
        assert len(pool.available_pages) == 0
        context.new_page.assert_not_called()

    @pytest.mark.asyncio
    async def test_acquire_replaces_closed_page(self):
        """If a pooled page is closed, a new page is created."""
        crawler = _make_crawler()
        pool = PagePool(crawler, max_pages=5)
        closed_page = _make_mock_page(is_closed=True)
        new_page = _make_mock_page()
        pool.available_pages.append(closed_page)
        context = _make_mock_context(new_page)

        result = await pool.acquire_page(context)
        assert result is new_page
        context.new_page.assert_called_once()

    @pytest.mark.asyncio
    async def test_acquire_replaces_page_on_check_exception(self):
        """If checking page availability throws, a new page is created."""
        crawler = _make_crawler()
        pool = PagePool(crawler, max_pages=5)
        bad_page = MagicMock()
        bad_page.is_closed.side_effect = RuntimeError("check failed")
        new_page = _make_mock_page()
        pool.available_pages.append(bad_page)
        context = _make_mock_context(new_page)

        result = await pool.acquire_page(context)
        assert result is new_page
        context.new_page.assert_called_once()


class TestPagePoolRelease:
    @pytest.mark.asyncio
    async def test_release_returns_page_to_pool(self):
        crawler = _make_crawler()
        pool = PagePool(crawler, max_pages=5)
        page = _make_mock_page()
        pool.in_use_pages.add(page)

        await pool.release_page(page)
        assert page not in pool.in_use_pages
        assert page in pool.available_pages

    @pytest.mark.asyncio
    async def test_release_ignores_unknown_page(self):
        """Releasing a page not in in_use_pages does nothing."""
        crawler = _make_crawler()
        pool = PagePool(crawler, max_pages=5)
        page = _make_mock_page()

        await pool.release_page(page)
        assert page not in pool.available_pages
        assert page not in pool.in_use_pages

    @pytest.mark.asyncio
    async def test_release_removes_listeners(self):
        crawler = _make_crawler()
        pool = PagePool(crawler, max_pages=5)
        page = _make_mock_page()
        pool.in_use_pages.add(page)

        await pool.release_page(page)
        page.remove_listener.assert_any_call("download", None)
        page.remove_listener.assert_any_call("response", None)

    @pytest.mark.asyncio
    async def test_release_handles_listener_exception(self):
        """remove_listener exception should not prevent page return."""
        crawler = _make_crawler()
        pool = PagePool(crawler, max_pages=5)
        page = _make_mock_page()
        page.remove_listener.side_effect = RuntimeError("no listener")
        pool.in_use_pages.add(page)

        await pool.release_page(page)
        assert page in pool.available_pages


class TestPagePoolCloseAll:
    @pytest.mark.asyncio
    async def test_close_all_closes_available_and_in_use(self):
        crawler = _make_crawler()
        pool = PagePool(crawler, max_pages=5)
        page1 = _make_mock_page()
        page2 = _make_mock_page()
        pool.available_pages.append(page1)
        pool.in_use_pages.add(page2)

        await pool.close_all()
        page1.close.assert_called_once()
        page2.close.assert_called_once()
        assert len(pool.available_pages) == 0
        assert len(pool.in_use_pages) == 0

    @pytest.mark.asyncio
    async def test_close_all_handles_close_exception(self):
        crawler = _make_crawler()
        pool = PagePool(crawler, max_pages=5)
        page = _make_mock_page()
        page.close.side_effect = RuntimeError("close failed")
        pool.available_pages.append(page)

        await pool.close_all()  # should not raise
        assert len(pool.available_pages) == 0

    @pytest.mark.asyncio
    async def test_close_all_empty_pool(self):
        crawler = _make_crawler()
        pool = PagePool(crawler, max_pages=5)
        await pool.close_all()  # should not raise
        assert len(pool.available_pages) == 0
        assert len(pool.in_use_pages) == 0
