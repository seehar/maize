"""
Tests for middleware lifecycle open/close/from_crawler and edge cases.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from maize.aio.classic.downloader import AioHttpDownloader, HTTPXDownloader, PatchrightDownloader, PlaywrightDownloader
from maize.aio.classic.middleware import (
    DefaultHeadersMiddleware,
    DepthMiddleware as ClassicDepth,
    DownloaderMiddleware as ClassicDownloader,
    HttpErrorMiddleware as ClassicHttpError,
    ItemCleanerMiddleware as ClassicCleaner,
    ItemValidationMiddleware as ClassicValidation,
    PipelineMiddleware as ClassicPipeline,
    RetryMiddleware as ClassicRetry,
    SpiderMiddleware as ClassicSpider,
    UserAgentMiddleware as ClassicUA,
)
from maize.aio.classic.pipeline import BasePipeline, EmptyPipeline
from maize.base.downloader.base_downloader import BaseDownloader
from maize.base.interface.spider_interface import SpiderInterface
from maize.command.code_template.spider_template import SpiderTemplate
from maize.common.http.request import Request
from maize.common.http.response import Response
from maize.common.items import Item
from maize.middlewares.base_middleware import (
    BaseMiddleware,
    DownloaderMiddleware,
)
from maize.middlewares.downloader.retry_middleware import RetryMiddleware
from maize.middlewares.downloader.user_agent_middleware import UserAgentMiddleware
from maize.middlewares.pipeline.cleaner import ItemCleanerMiddleware
from maize.middlewares.pipeline.validation import ItemValidationMiddleware
from maize.middlewares.spider.depth_middleware import DepthMiddleware
from maize.middlewares.spider.http_error_middleware import HttpErrorMiddleware
from maize.settings import SpiderSettings
from maize.utils.log_util import set_spider_settings


def _make_spider():
    return MagicMock()


# ---------------------------------------------------------------------------
# BaseMiddleware lifecycle
# ---------------------------------------------------------------------------


class TestBaseMiddlewareLifecycle:
    """Cover BaseMiddleware abstract open/close (lines 51, 60)."""

    def test_base_middleware_open_abstract(self):
        assert BaseMiddleware.open.__isabstractmethod__ is True

    def test_base_middleware_close_abstract(self):
        assert BaseMiddleware.close.__isabstractmethod__ is True

    def test_from_crawler(self):
        crawler = MagicMock()
        crawler.settings = SpiderSettings()
        mw = DownloaderMiddleware.from_crawler(crawler)
        assert mw.settings is crawler.settings


# ---------------------------------------------------------------------------
# RetryMiddleware lifecycle
# ---------------------------------------------------------------------------


class TestRetryMiddlewareLifecycle:
    """Cover RetryMiddleware.open/close (lines 40, 43)."""

    @pytest.mark.asyncio
    async def test_open_is_noop(self):
        mw = RetryMiddleware(SpiderSettings())
        await mw.open()

    @pytest.mark.asyncio
    async def test_close_is_noop(self):
        mw = RetryMiddleware(SpiderSettings())
        await mw.close()

    @pytest.mark.asyncio
    async def test_process_request_no_retry_codes(self):
        """Normal request passes through when no retry codes match."""
        mw = RetryMiddleware(SpiderSettings(), retry_http_codes=[500])
        req = Request("https://example.com")
        spider = _make_spider()
        result = await mw.process_request(req, spider)
        assert result is req

    @pytest.mark.asyncio
    async def test_process_exception_max_retry_returns_none(self):
        """Exceeding max_retry returns None. retry_count starts at 0, max=1 means 1 retry allowed."""
        mw = RetryMiddleware(SpiderSettings(), max_retry_count=1, retry_exceptions=[ConnectionError])
        req = Request("https://example.com")
        req.meta["retry_count"] = 1  # already retried once, now at limit
        spider = _make_spider()
        result = await mw.process_exception(req, ConnectionError("boom"), spider)
        assert result is None

    @pytest.mark.asyncio
    async def test_process_exception_triggers_retry(self):
        """Exception matching retry exceptions triggers retry."""
        mw = RetryMiddleware(SpiderSettings(), retry_exceptions=[ConnectionError])
        req = Request("https://example.com")
        spider = _make_spider()
        result = await mw.process_exception(req, ConnectionError("boom"), spider)
        assert isinstance(result, Request)

    @pytest.mark.asyncio
    async def test_process_exception_no_matching_exception(self):
        """Non-matching exception returns None."""
        mw = RetryMiddleware(SpiderSettings(), retry_exceptions=[ConnectionError])
        req = Request("https://example.com")
        spider = _make_spider()
        result = await mw.process_exception(req, ValueError("not matching"), spider)
        assert result is None

    @pytest.mark.asyncio
    async def test_retry_with_delay(self):
        """Retry with delay > 0 calls asyncio.sleep (line 156)."""

        mw = RetryMiddleware(SpiderSettings(), max_retry_count=2, retry_exceptions=[ConnectionError], retry_delay=1)
        req = Request("https://example.com")
        spider = _make_spider()
        with patch("maize.middlewares.downloader.retry_middleware.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            result = await mw.process_exception(req, ConnectionError("boom"), spider)
            assert isinstance(result, Request)
            mock_sleep.assert_called_once()

    @pytest.mark.asyncio
    async def test_retry_with_exponential_backoff(self):
        mw = RetryMiddleware(
            SpiderSettings(),
            max_retry_count=3,
            retry_exceptions=[ConnectionError],
            retry_delay=1,
            exponential_backoff=True,
        )
        req = Request("https://example.com")
        spider = _make_spider()
        with patch("maize.middlewares.downloader.retry_middleware.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            result = await mw.process_exception(req, ConnectionError("boom"), spider)
            assert isinstance(result, Request)
            mock_sleep.assert_called_once()


# ---------------------------------------------------------------------------
# UserAgentMiddleware sequential mode (line 88-89)
# ---------------------------------------------------------------------------


class TestUserAgentMiddlewareSequential:
    """Cover UserAgentMiddleware sequential mode (lines 88-89)."""

    @pytest.mark.asyncio
    async def test_sequential_mode_cycles(self):
        mw = UserAgentMiddleware(SpiderSettings(), user_agent_list=["UA-A", "UA-B", "UA-C"], mode="sequential")
        spider = _make_spider()

        req1 = Request("https://example.com/1")
        await mw.process_request(req1, spider)
        assert req1.headers["User-Agent"] == "UA-A"

        req2 = Request("https://example.com/2")
        await mw.process_request(req2, spider)
        assert req2.headers["User-Agent"] == "UA-B"

        req3 = Request("https://example.com/3")
        await mw.process_request(req3, spider)
        assert req3.headers["User-Agent"] == "UA-C"

        # Wraps around
        req4 = Request("https://example.com/4")
        await mw.process_request(req4, spider)
        assert req4.headers["User-Agent"] == "UA-A"


# ---------------------------------------------------------------------------
# DepthMiddleware lifecycle (lines 31, 34)
# ---------------------------------------------------------------------------


class TestDepthMiddlewareLifecycle:
    """Cover DepthMiddleware open/close (lines 31, 34)."""

    @pytest.mark.asyncio
    async def test_open_is_noop(self):
        mw = DepthMiddleware(SpiderSettings())
        await mw.open()

    @pytest.mark.asyncio
    async def test_close_is_noop(self):
        mw = DepthMiddleware(SpiderSettings())
        await mw.close()


class TestSpiderInterfaceAbstractRaises:
    """Cover SpiderInterface abstract method raise statements."""

    def test_spider_interface_open_abstract(self):
        assert SpiderInterface.open.__isabstractmethod__ is True

    def test_spider_interface_close_abstract(self):
        assert SpiderInterface.close.__isabstractmethod__ is True


# ---------------------------------------------------------------------------
# HttpErrorMiddleware lifecycle (line 37)
# ---------------------------------------------------------------------------


class TestHttpErrorMiddlewareLifecycle:
    """Cover HttpErrorMiddleware.open (line 37)."""

    @pytest.mark.asyncio
    async def test_open_is_noop(self):
        mw = HttpErrorMiddleware(SpiderSettings())
        await mw.open()


# ---------------------------------------------------------------------------
# ItemValidationMiddleware open (line 26) + _log_validation_error (line 80)
# ---------------------------------------------------------------------------


class TestValidationMiddlewareLifecycle:
    """Cover ItemValidationMiddleware.open (line 26) and error logging (line 80)."""

    @pytest.mark.asyncio
    async def test_open_is_noop(self):
        mw = ItemValidationMiddleware(SpiderSettings())
        await mw.open()

    @pytest.mark.asyncio
    async def test_missing_required_field_logs_error(self):
        mw = ItemValidationMiddleware(SpiderSettings(), required_fields=["title"], drop_invalid_items=False)

        class MyItem(Item):
            __table_name__: str = "test"
            title: str = ""

        item = MyItem(title="")
        spider = _make_spider()
        result = await mw.process_item_before(item, spider)
        # Item is not dropped (drop_invalid_items=False), but error is logged
        assert result is item

    @pytest.mark.asyncio
    async def test_missing_field_attribute(self):
        """Item without the required field attribute triggers error."""
        mw = ItemValidationMiddleware(SpiderSettings(), required_fields=["nonexistent"])

        class MyItem(Item):
            __table_name__: str = "test"
            title: str = ""

        item = MyItem(title="hello")
        spider = _make_spider()
        result = await mw.process_item_before(item, spider)
        assert result is None  # dropped

    @pytest.mark.asyncio
    async def test_valid_item_passes(self):
        mw = ItemValidationMiddleware(SpiderSettings(), required_fields=["title"])

        class MyItem(Item):
            __table_name__: str = "test"
            title: str = ""

        item = MyItem(title="hello")
        spider = _make_spider()
        result = await mw.process_item_before(item, spider)
        assert result is item


# ---------------------------------------------------------------------------
# ItemCleanerMiddleware open/close (lines 36, 39) + from_crawler (line 137+)
# ---------------------------------------------------------------------------


class TestCleanerLifecycle:
    """Cover ItemCleanerMiddleware open/close (lines 36, 39)."""

    @pytest.mark.asyncio
    async def test_open_is_noop(self):
        mw = ItemCleanerMiddleware(SpiderSettings())
        await mw.open()

    @pytest.mark.asyncio
    async def test_close_is_noop(self):
        mw = ItemCleanerMiddleware(SpiderSettings())
        await mw.close()

    def test_from_crawler_with_no_settings_attrs(self):
        """from_crawler with settings that lack custom attrs uses defaults."""
        crawler = MagicMock()
        crawler.settings = MagicMock()
        # Remove custom attrs to trigger getattr defaults
        del crawler.settings.strip_whitespace
        del crawler.settings.remove_html
        del crawler.settings.normalize_whitespace
        del crawler.settings.empty_to_none
        del crawler.settings.excluded_fields
        mw = ItemCleanerMiddleware.from_crawler(crawler)
        assert isinstance(mw, ItemCleanerMiddleware)
        assert mw.strip_whitespace is True
        assert mw.remove_html is False


# ---------------------------------------------------------------------------
# SpiderInterface abstract raises (lines 24, 33, 42, 52)
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# BaseDownloader abstract raises (lines 86, 110)
# ---------------------------------------------------------------------------


class TestBaseDownloaderAbstractRaises:
    """Cover BaseDownloader abstract method raise statements."""

    def test_download_abstract(self):
        assert BaseDownloader.download.__isabstractmethod__ is True

    def test_structure_response_abstract(self):
        assert BaseDownloader.structure_response.__isabstractmethod__ is True


# ---------------------------------------------------------------------------
# SpiderTemplate (lines 9, 12)
# ---------------------------------------------------------------------------


class TestSpiderTemplateExecution:
    """Cover spider_template.py lines 9 and 12."""

    @pytest.mark.asyncio
    async def test_start_requests_yields_request(self):
        results = []
        async for req in SpiderTemplate().start_requests():
            results.append(req)
        assert len(results) == 1
        assert isinstance(results[0], Request)

    @pytest.mark.asyncio
    async def test_parse_logs_response(self):
        set_spider_settings(SpiderSettings())
        spider = SpiderTemplate()
        await spider.open()
        req = Request("https://example.com")
        resp = Response(url="https://example.com", headers={}, request=req, text="hello", status=200)
        await spider.parse(resp)
        await spider.close()


# ---------------------------------------------------------------------------
# Classic middleware/pipeline __init__ re-exports
# ---------------------------------------------------------------------------


class TestClassicReExports:
    """Cover aio.classic.middleware and pipeline __init__ re-exports."""

    def test_middleware_re_exports(self):
        assert DefaultHeadersMiddleware is not None
        assert ClassicDepth is not None
        assert ClassicDownloader is not None
        assert ClassicHttpError is not None
        assert ClassicCleaner is not None
        assert ClassicValidation is not None
        assert ClassicPipeline is not None
        assert ClassicRetry is not None
        assert ClassicSpider is not None
        assert ClassicUA is not None

    def test_pipeline_re_exports(self):
        assert BasePipeline is not None
        assert EmptyPipeline is not None


# ---------------------------------------------------------------------------
# Downloader __init__ optional imports (lines 6-7, 11-12)
# ---------------------------------------------------------------------------


class TestDownloaderInitOptional:
    """Cover aio.classic.downloader.__init__ optional import fallbacks."""

    def test_patchright_imported(self):
        assert PatchrightDownloader is not None

    def test_playwright_imported(self):
        assert PlaywrightDownloader is not None

    def test_aiohttp_and_httpx_always_imported(self):
        assert AioHttpDownloader is not None
        assert HTTPXDownloader is not None
