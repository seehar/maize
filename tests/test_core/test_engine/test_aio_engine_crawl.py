"""
Tests for AioEngine crawl loop, _crawl_start_requests, _crawl_task_requests,
_handle_success_response callback/transform paths, enqueue/_get_next_request redis paths.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from maize.common.http.request import Request
from maize.common.http.response import Response
from maize.common.items import Item
from maize.core.engine.aio_engine import AioEngine
from maize.settings import SpiderSettings


def _make_engine():
    crawler = MagicMock()
    crawler.settings = SpiderSettings()
    crawler.idle.return_value = True
    engine = AioEngine(crawler)
    engine.spider = MagicMock()
    engine.spider.stats_collector.record_download_success = AsyncMock()
    engine.spider.stats_collector.record_download_fail = AsyncMock()
    engine.spider.stats_collector.record_parse_success = AsyncMock()
    engine.spider.stats_collector.record_parse_fail = AsyncMock()
    engine.scheduler = MagicMock()
    engine.scheduler.put = AsyncMock()
    engine.scheduler.get = AsyncMock(return_value=None)
    engine.scheduler.get_by_priority = AsyncMock(return_value=None)
    engine.scheduler.qsize.return_value = 0
    engine.downloader = MagicMock()
    engine.downloader.idle.return_value = True
    engine.downloader.fetch = AsyncMock()
    engine.processor = MagicMock()
    engine.processor.enqueue = AsyncMock()
    engine.processor.idle.return_value = True
    engine.task_manager = MagicMock()
    engine.task_manager.all_done.return_value = True
    engine.task_manager.semaphore = MagicMock()
    engine.task_manager.semaphore.acquire = AsyncMock()
    engine.task_manager.create_task = MagicMock()
    return engine


class TestHandleSuccessResponseCallback:
    """Cover _handle_success_response callback/transform paths."""

    @pytest.mark.asyncio
    async def test_sync_callback_with_transform(self):
        """Callback returning a generator triggers transform + stats."""
        engine = _make_engine()
        engine.spider_middleware_manager = None
        req = Request("https://example.com")

        def callback(response):
            yield Request("https://example.com/next")
            yield Item()

        engine.spider.parse = callback
        resp = Response(url="https://example.com", headers={}, request=req, status=200, text="ok")
        result = await engine._handle_success_response(resp, req)
        assert result is not None
        engine.spider.stats_collector.record_parse_success.assert_called_once()

    @pytest.mark.asyncio
    async def test_callback_raises_records_fail(self):
        """Callback raising Exception records parse fail."""
        engine = _make_engine()
        engine.spider_middleware_manager = None
        req = Request("https://example.com")

        def bad_callback(response):
            raise RuntimeError("parse error")

        engine.spider.parse = bad_callback
        resp = Response(url="https://example.com", headers={}, request=req, status=200, text="ok")
        result = await engine._handle_success_response(resp, req)
        assert result is None
        engine.spider.stats_collector.record_parse_fail.assert_called_once()

    @pytest.mark.asyncio
    async def test_spider_middleware_input_false(self):
        """When spider middleware process_spider_input returns False, returns None."""
        engine = _make_engine()
        engine.spider_middleware_manager = MagicMock()
        engine.spider_middleware_manager.process_spider_input = AsyncMock(return_value=False)
        req = Request("https://example.com")
        resp = Response(url="https://example.com", headers={}, request=req, status=200, text="ok")
        result = await engine._handle_success_response(resp, req)
        assert result is None

    @pytest.mark.asyncio
    async def test_spider_middleware_input_exception(self):
        """When spider middleware process_spider_input raises, returns None."""
        engine = _make_engine()
        engine.spider_middleware_manager = MagicMock()
        engine.spider_middleware_manager.process_spider_input = AsyncMock(side_effect=RuntimeError("mw error"))
        req = Request("https://example.com")
        resp = Response(url="https://example.com", headers={}, request=req, status=200, text="ok")
        result = await engine._handle_success_response(resp, req)
        assert result is None

    @pytest.mark.asyncio
    async def test_callback_no_output(self):
        """Callback returning None/falsy skips transform."""
        engine = _make_engine()
        engine.spider_middleware_manager = None
        req = Request("https://example.com")
        engine.spider.parse = MagicMock(return_value=None)
        resp = Response(url="https://example.com", headers={}, request=req, status=200, text="ok")
        result = await engine._handle_success_response(resp, req)
        assert result is None


class TestHandleErrorResponseTransform:
    """Cover _handle_error_response transform path (lines 379-381)."""

    @pytest.mark.asyncio
    async def test_error_callback_with_generator(self):
        """Error callback returning a generator triggers transform."""
        engine = _make_engine()

        def err_cb(request):
            yield Request("https://example.com/retry")

        req = Request("https://example.com", error_callback=err_cb)
        result = await engine._handle_error_response(req)
        assert result is not None
        engine.spider.stats_collector.record_parse_fail.assert_called_once()

    @pytest.mark.asyncio
    async def test_error_callback_raises(self):
        """Error callback raising logs error and returns None."""
        engine = _make_engine()

        def bad_err_cb(request):
            raise RuntimeError("error cb failed")

        req = Request("https://example.com", error_callback=bad_err_cb)
        result = await engine._handle_error_response(req)
        assert result is None


class TestEnqueueAndGetNextRequest:
    """Cover enqueue_request and _get_next_request."""

    @pytest.mark.asyncio
    async def test_enqueue_request_no_redis(self):
        engine = _make_engine()
        req = Request("https://example.com")
        await engine.enqueue_request(req)
        engine.scheduler.put.assert_called_once_with(req)

    @pytest.mark.asyncio
    async def test_get_next_request_empty(self):
        engine = _make_engine()
        engine.scheduler.get = AsyncMock(return_value=None)
        engine.scheduler.get_by_priority = AsyncMock(return_value=None)
        result = await engine._get_next_request()
        assert result is None

    @pytest.mark.asyncio
    async def test_get_next_request_returns_request(self):
        engine = _make_engine()
        req = Request("https://example.com")
        engine.scheduler.get = AsyncMock(return_value=req)
        engine.scheduler.get_by_priority = AsyncMock(return_value=req)
        engine.crawler.spider.gte_priority = None
        result = await engine._get_next_request()
        assert result is req


class TestCrawlStartRequests:
    """Cover _crawl_start_requests with a simple flow."""

    @pytest.mark.asyncio
    async def test_crawl_start_requests_completes(self):
        """Engine processes start_requests generator then stops."""
        engine = _make_engine()
        engine.spider_middleware_manager = None
        engine.spider.__spider_type__ = "spider"

        async def gen():
            yield Request("https://example.com")

        engine.start_requests = gen()
        engine.start_requests_running = True
        engine.scheduler.get = AsyncMock(return_value=None)
        engine.scheduler.get_by_priority = AsyncMock(return_value=None)

        # _crawl will be called; mock it to avoid full fetch
        engine._crawl = AsyncMock()

        # After the generator is exhausted and everything idle, start_requests_running becomes False
        await engine._crawl_start_requests()
        assert engine.start_requests_running is False

    @pytest.mark.asyncio
    async def test_crawl_start_requests_with_middleware(self):
        """_crawl_start_requests applies spider middleware to start_requests."""
        engine = _make_engine()
        engine.spider_middleware_manager = MagicMock()

        async def gen():
            yield Request("https://example.com")

        # process_start_requests returns a passthrough async generator
        async def passthrough(sr, spider):
            async for r in sr:
                yield r

        engine.spider_middleware_manager.process_start_requests = passthrough
        engine.start_requests = gen()
        engine.start_requests_running = True
        engine.scheduler.get = AsyncMock(return_value=None)
        engine.scheduler.get_by_priority = AsyncMock(return_value=None)
        engine._crawl = AsyncMock()

        await engine._crawl_start_requests()
        assert engine.start_requests_running is False


class TestProcessResponseMiddleware:
    """Cover _process_response_middleware paths."""

    @pytest.mark.asyncio
    async def test_no_middleware_returns_response(self):
        engine = _make_engine()
        engine.downloader_middleware_manager = None
        req = Request("https://example.com")
        resp = Response(url="https://example.com", headers={}, request=req, status=200, text="ok")
        result = await engine._process_response_middleware(req, resp)
        assert result is resp

    @pytest.mark.asyncio
    async def test_middleware_returns_request(self):
        """When process_response returns Request, it's enqueued and None returned."""
        engine = _make_engine()
        engine.downloader_middleware_manager = MagicMock()
        retry_req = Request("https://retry.com")
        engine.downloader_middleware_manager.process_response = AsyncMock(return_value=retry_req)
        req = Request("https://example.com")
        resp = Response(url="https://example.com", headers={}, request=req, status=200, text="ok")
        result = await engine._process_response_middleware(req, resp)
        assert result is None
        engine.scheduler.put.assert_called_once_with(retry_req)


class TestProcessRequestMiddleware:
    """Cover _process_request_middleware paths."""

    @pytest.mark.asyncio
    async def test_no_middleware_returns_request(self):
        engine = _make_engine()
        engine.downloader_middleware_manager = None
        req = Request("https://example.com")
        result = await engine._process_request_middleware(req)
        assert result is req

    @pytest.mark.asyncio
    async def test_middleware_returns_response(self):
        engine = _make_engine()
        engine.downloader_middleware_manager = MagicMock()
        req = Request("https://example.com")
        resp = Response(url="https://example.com", headers={}, request=req, status=200, text="ok")
        engine.downloader_middleware_manager.process_request = AsyncMock(return_value=resp)
        result = await engine._process_request_middleware(req)
        assert result is resp

    @pytest.mark.asyncio
    async def test_middleware_returns_none(self):
        engine = _make_engine()
        engine.downloader_middleware_manager = MagicMock()
        engine.downloader_middleware_manager.process_request = AsyncMock(return_value=None)
        req = Request("https://example.com")
        result = await engine._process_request_middleware(req)
        assert result is None
