"""
Tests for MiddlewareManager exception/continue/skip/drop paths
covering all remaining missed lines.
"""

from unittest.mock import MagicMock

import pytest

from maize.common.http.request import Request
from maize.common.http.response import Response
from maize.common.items import Item
from maize.middlewares.base_middleware import (
    DownloaderMiddleware,
    PipelineMiddleware,
    SpiderMiddleware,
)
from maize.middlewares.middleware_manager import (
    DownloaderMiddlewareManager,
    PipelineMiddlewareManager,
    SpiderMiddlewareManager,
)
from maize.settings import SpiderSettings
from maize.utils.log_util import LoggerManager, set_spider_settings


def _make_crawler():
    crawler = MagicMock()
    crawler.settings = SpiderSettings()
    set_spider_settings(crawler.settings)
    # Clear any stale loggers that may have MagicMock handlers from other tests
    LoggerManager.logger.clear()
    return crawler


def _make_request():
    return Request("https://example.com")


def _make_response():
    req = _make_request()
    return Response(url="https://example.com", headers={}, request=req, status=200, text="ok")


# ---------------------------------------------------------------------------
# DownloaderMiddlewareManager: process_request with non-DownloaderMiddleware
# ---------------------------------------------------------------------------


class TestProcessRequestNonDownloaderMiddleware:
    """Cover line 123: non-DownloaderMiddleware is skipped with continue."""

    @pytest.mark.asyncio
    async def test_non_downloader_middleware_skipped(self):
        crawler = _make_crawler()
        manager = DownloaderMiddlewareManager(crawler, {})

        # Add a non-DownloaderMiddleware
        non_mw = MagicMock()  # not an instance of DownloaderMiddleware
        manager.middlewares = [(non_mw, 1)]

        req = _make_request()
        spider = MagicMock()
        result = await manager.process_request(req, spider)
        assert result is req  # passes through


# ---------------------------------------------------------------------------
# DownloaderMiddlewareManager: process_response with non-DownloaderMiddleware
# ---------------------------------------------------------------------------


class TestProcessResponseNonDownloaderMiddleware:
    """Cover line 166: non-DownloaderMiddleware skipped in process_response."""

    @pytest.mark.asyncio
    async def test_non_downloader_middleware_skipped(self):
        crawler = _make_crawler()
        manager = DownloaderMiddlewareManager(crawler, {})
        non_mw = MagicMock()
        manager.middlewares = [(non_mw, 1)]

        req = _make_request()
        resp = _make_response()
        spider = MagicMock()
        result = await manager.process_response(req, resp, spider)
        assert result is resp


# ---------------------------------------------------------------------------
# DownloaderMiddlewareManager: process_exception exception handling
# ---------------------------------------------------------------------------


class TestProcessExceptionPaths:
    """Cover lines 207, 217-220: process_exception skip/exception paths."""

    @pytest.mark.asyncio
    async def test_non_downloader_middleware_skipped(self):
        crawler = _make_crawler()
        manager = DownloaderMiddlewareManager(crawler, {})
        non_mw = MagicMock()
        manager.middlewares = [(non_mw, 1)]

        req = _make_request()
        result = await manager.process_exception(req, ValueError("err"), MagicMock())
        assert result is None

    @pytest.mark.asyncio
    async def test_middleware_exception_continues(self):
        """When middleware.process_exception raises, continues to next."""
        crawler = _make_crawler()
        manager = DownloaderMiddlewareManager(crawler, {})

        class FailingMW(DownloaderMiddleware):
            async def process_exception(self, request, exception, spider):
                raise RuntimeError("mw error")

        class GoodMW(DownloaderMiddleware):
            async def process_exception(self, request, exception, spider):
                return request

        manager.middlewares = [(FailingMW(SpiderSettings()), 1), (GoodMW(SpiderSettings()), 2)]
        req = _make_request()
        result = await manager.process_exception(req, ValueError("err"), MagicMock())
        assert result is req


# ---------------------------------------------------------------------------
# SpiderMiddlewareManager: process_spider_input exception → process_spider_exception
# ---------------------------------------------------------------------------


class TestSpiderInputException:
    """Cover lines 245, 254, 276, 280-283, 305, 312-314, 333, 337-340."""

    @pytest.mark.asyncio
    async def test_non_spider_middleware_skipped_in_input(self):
        crawler = _make_crawler()
        manager = SpiderMiddlewareManager(crawler, {})
        non_mw = MagicMock()
        manager.middlewares = [(non_mw, 1)]

        resp = _make_response()
        result = await manager.process_spider_input(resp, MagicMock())
        assert result is True

    @pytest.mark.asyncio
    async def test_spider_input_exception_handled_by_exception_handler(self):
        """When process_spider_input raises and exception handler returns result, returns False."""
        crawler = _make_crawler()
        manager = SpiderMiddlewareManager(crawler, {})

        class FailingInputMW(SpiderMiddleware):
            async def process_spider_input(self, response, spider):
                raise ValueError("input error")

        class ExceptionHandlerMW(SpiderMiddleware):
            async def process_spider_exception(self, response, exception, spider):
                async def gen():
                    yield Request("https://example.com/retry")

                return gen()

        manager.middlewares = [(FailingInputMW(SpiderSettings()), 1), (ExceptionHandlerMW(SpiderSettings()), 2)]
        resp = _make_response()
        result = await manager.process_spider_input(resp, MagicMock())
        assert result is False

    @pytest.mark.asyncio
    async def test_spider_input_exception_not_handled_reraises(self):
        """When exception handler returns None, original exception re-raises."""
        crawler = _make_crawler()
        manager = SpiderMiddlewareManager(crawler, {})

        class FailingInputMW(SpiderMiddleware):
            async def process_spider_input(self, response, spider):
                raise ValueError("input error")

        manager.middlewares = [(FailingInputMW(SpiderSettings()), 1)]
        resp = _make_response()
        with pytest.raises(ValueError, match="input error"):
            await manager.process_spider_input(resp, MagicMock())

    @pytest.mark.asyncio
    async def test_process_spider_output_non_spider_skipped(self):
        """Non-SpiderMiddleware is skipped in process_spider_output."""
        crawler = _make_crawler()
        manager = SpiderMiddlewareManager(crawler, {})
        non_mw = MagicMock()
        manager.middlewares = [(non_mw, 1)]

        async def gen():
            yield Request("https://example.com")

        resp = _make_response()
        results = []
        async for item in manager.process_spider_output(resp, gen(), MagicMock()):
            results.append(item)
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_process_spider_output_middleware_exception_continues(self):
        """When process_spider_output raises synchronously, continues with original result."""
        crawler = _make_crawler()
        manager = SpiderMiddlewareManager(crawler, {})

        class FailingOutputMW(SpiderMiddleware):
            async def process_spider_output(self, response, result, spider):
                raise RuntimeError("output error")
                yield  # type: ignore[unreachable]

        manager.middlewares = [(FailingOutputMW(SpiderSettings()), 1)]

        async def gen():
            yield Request("https://example.com")

        resp = _make_response()

        # The middleware's process_spider_output returns an async gen that raises on iteration.
        # But calling it doesn't raise, so the manager's try/catch doesn't trigger.
        # The exception happens at `async for item in result` (line 286) which is uncaught.
        # We need to test that calling a non-async-gen-raising middleware is caught.
        # Instead, let's override process_spider_output to raise immediately:
        def _raising_output(_self, _response, _result, _spider):
            raise RuntimeError("sync error")

        FailingOutputMW.process_spider_output = _raising_output

        results = []
        async for item in manager.process_spider_output(resp, gen(), MagicMock()):
            results.append(item)
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_process_spider_exception_non_spider_skipped(self):
        crawler = _make_crawler()
        manager = SpiderMiddlewareManager(crawler, {})
        non_mw = MagicMock()
        manager.middlewares = [(non_mw, 1)]

        resp = _make_response()
        result = await manager.process_spider_exception(resp, ValueError("err"), MagicMock())
        assert result is None

    @pytest.mark.asyncio
    async def test_process_spider_exception_returns_result(self):
        crawler = _make_crawler()
        manager = SpiderMiddlewareManager(crawler, {})

        class HandlerMW(SpiderMiddleware):
            async def process_spider_exception(self, response, exception, spider):
                async def gen():
                    yield Request("https://example.com/retry")

                return gen()

        manager.middlewares = [(HandlerMW(SpiderSettings()), 1)]
        resp = _make_response()
        result = await manager.process_spider_exception(resp, ValueError("err"), MagicMock())
        assert result is not None

    @pytest.mark.asyncio
    async def test_process_spider_exception_middleware_raises(self):
        """When process_spider_exception raises, continues to next."""
        crawler = _make_crawler()
        manager = SpiderMiddlewareManager(crawler, {})

        class FailingMW(SpiderMiddleware):
            async def process_spider_exception(self, response, exception, spider):
                raise RuntimeError("handler error")

        class GoodMW(SpiderMiddleware):
            async def process_spider_exception(self, response, exception, spider):
                return None

        manager.middlewares = [(FailingMW(SpiderSettings()), 1), (GoodMW(SpiderSettings()), 2)]
        resp = _make_response()
        result = await manager.process_spider_exception(resp, ValueError("err"), MagicMock())
        assert result is None

    @pytest.mark.asyncio
    async def test_process_start_requests_non_spider_skipped(self):
        crawler = _make_crawler()
        manager = SpiderMiddlewareManager(crawler, {})
        non_mw = MagicMock()
        manager.middlewares = [(non_mw, 1)]

        async def gen():
            yield Request("https://example.com")

        results = []
        async for r in manager.process_start_requests(gen(), MagicMock()):
            results.append(r)
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_process_start_requests_middleware_exception(self):
        """When process_start_requests raises, continues with original generator."""
        crawler = _make_crawler()
        manager = SpiderMiddlewareManager(crawler, {})

        class FailingMW(SpiderMiddleware):
            def process_start_requests(self, start_requests, spider):
                raise RuntimeError("start error")

        manager.middlewares = [(FailingMW(SpiderSettings()), 1)]

        async def gen():
            yield Request("https://example.com")

        results = []
        async for r in manager.process_start_requests(gen(), MagicMock()):
            results.append(r)
        assert len(results) == 1


# ---------------------------------------------------------------------------
# PipelineMiddlewareManager: exception/drop paths
# ---------------------------------------------------------------------------


class TestPipelineMiddlewareExceptionPaths:
    """Cover lines 367, 377-380, 397, 407-410."""

    @pytest.mark.asyncio
    async def test_non_pipeline_middleware_skipped_before(self):
        crawler = _make_crawler()
        manager = PipelineMiddlewareManager(crawler, {})
        non_mw = MagicMock()
        manager.middlewares = [(non_mw, 1)]

        item = Item()
        result = await manager.process_item_before(item, MagicMock())
        assert result is item

    @pytest.mark.asyncio
    async def test_process_item_before_exception_continues(self):
        crawler = _make_crawler()
        manager = PipelineMiddlewareManager(crawler, {})

        class FailingMW(PipelineMiddleware):
            async def process_item_before(self, item, spider):
                raise RuntimeError("before error")

        class GoodMW(PipelineMiddleware):
            async def process_item_before(self, item, spider):
                return item

        manager.middlewares = [(FailingMW(SpiderSettings()), 1), (GoodMW(SpiderSettings()), 2)]
        item = Item()
        result = await manager.process_item_before(item, MagicMock())
        assert result is item

    @pytest.mark.asyncio
    async def test_non_pipeline_middleware_skipped_after(self):
        crawler = _make_crawler()
        manager = PipelineMiddlewareManager(crawler, {})
        non_mw = MagicMock()
        manager.middlewares = [(non_mw, 1)]

        item = Item()
        result = await manager.process_item_after(item, MagicMock())
        assert result is item

    @pytest.mark.asyncio
    async def test_process_item_after_exception_continues(self):
        crawler = _make_crawler()
        manager = PipelineMiddlewareManager(crawler, {})

        class FailingMW(PipelineMiddleware):
            async def process_item_after(self, item, spider):
                raise RuntimeError("after error")

        class GoodMW(PipelineMiddleware):
            async def process_item_after(self, item, spider):
                return item

        manager.middlewares = [(FailingMW(SpiderSettings()), 1), (GoodMW(SpiderSettings()), 2)]
        item = Item()
        result = await manager.process_item_after(item, MagicMock())
        assert result is item

    @pytest.mark.asyncio
    async def test_process_item_after_drops_item(self):
        crawler = _make_crawler()
        manager = PipelineMiddlewareManager(crawler, {})

        class DroppingMW(PipelineMiddleware):
            async def process_item_after(self, item, spider):
                return None

        manager.middlewares = [(DroppingMW(SpiderSettings()), 1)]
        item = Item()
        result = await manager.process_item_after(item, MagicMock())
        assert result is None
