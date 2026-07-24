"""
Tests for AioEngine fetch/download/middleware/handle paths.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from maize.common.http.request import Request
from maize.common.http.response import Response
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
    engine.processor = MagicMock()
    engine.processor.enqueue = AsyncMock()
    engine.processor.idle.return_value = True
    engine.task_manager = MagicMock()
    engine.task_manager.all_done.return_value = True
    return engine


class TestAioEngineFetch:
    """Test AioEngine._fetch and its branches."""

    @pytest.mark.asyncio
    async def test_fetch_middleware_drops_request(self):
        """When process_request middleware returns None, _fetch returns None."""
        engine = _make_engine()
        req = Request("https://example.com")
        engine.downloader_middleware_manager = MagicMock()
        engine.downloader_middleware_manager.process_request = AsyncMock(return_value=None)

        result = await engine._fetch(req)
        assert result is None

    @pytest.mark.asyncio
    async def test_fetch_middleware_returns_response(self):
        """When process_request middleware returns Response, skip download."""
        engine = _make_engine()
        req = Request("https://example.com")
        resp = Response(url="https://example.com", headers={}, request=req, status=200, text="ok")
        engine.downloader_middleware_manager = MagicMock()
        engine.downloader_middleware_manager.process_request = AsyncMock(return_value=resp)
        engine.spider_middleware_manager = None
        engine.spider.parse = MagicMock(return_value=None)

        await engine._fetch(req)
        # Should call _handle_success_response with the response
        engine.spider.stats_collector.record_parse_success.assert_not_called()

    @pytest.mark.asyncio
    async def test_fetch_download_returns_none(self):
        """When _do_download returns None, _fetch returns None."""
        engine = _make_engine()
        req = Request("https://example.com")
        engine.downloader_middleware_manager = MagicMock()
        engine.downloader_middleware_manager.process_request = AsyncMock(return_value=req)
        engine._do_download = AsyncMock(return_value=None)

        result = await engine._fetch(req)
        assert result is None

    @pytest.mark.asyncio
    async def test_fetch_download_returns_request(self):
        """When _do_download returns a Request (retry), it's enqueued and _fetch returns None."""
        engine = _make_engine()
        req = Request("https://example.com")
        retry_req = Request("https://example.com/retry")
        engine.downloader_middleware_manager = MagicMock()
        engine.downloader_middleware_manager.process_request = AsyncMock(return_value=req)
        engine._do_download = AsyncMock(return_value=retry_req)

        result = await engine._fetch(req)
        assert result is None
        engine.scheduler.put.assert_called_once_with(retry_req)

    @pytest.mark.asyncio
    async def test_fetch_download_fail_with_error_callback(self):
        """When download_result.response is None, error response path is taken."""
        engine = _make_engine()
        req = Request("https://example.com")
        download_result = MagicMock()
        download_result.response = None
        download_result.reason = "timeout"
        engine.downloader_middleware_manager = MagicMock()
        engine.downloader_middleware_manager.process_request = AsyncMock(return_value=req)
        engine._do_download = AsyncMock(return_value=download_result)

        result = await engine._fetch(req)
        assert result is None
        engine.spider.stats_collector.record_download_fail.assert_called_once_with("timeout")

    @pytest.mark.asyncio
    async def test_fetch_success_response(self):
        """Successful download with response middleware returns transform output."""
        engine = _make_engine()
        req = Request("https://example.com")
        resp = Response(url="https://example.com", headers={}, request=req, status=200, text="ok")
        download_result = MagicMock()
        download_result.response = resp
        engine.downloader_middleware_manager = MagicMock()
        engine.downloader_middleware_manager.process_request = AsyncMock(return_value=req)
        engine.downloader_middleware_manager.process_response = AsyncMock(return_value=resp)
        engine._do_download = AsyncMock(return_value=download_result)
        engine.spider_middleware_manager = None
        engine.spider.parse = MagicMock(return_value=None)

        await engine._fetch(req)
        engine.spider.stats_collector.record_download_success.assert_called_once_with(200)

    @pytest.mark.asyncio
    async def test_fetch_response_middleware_drops(self):
        """When process_response middleware returns None, _fetch returns None."""
        engine = _make_engine()
        req = Request("https://example.com")
        resp = Response(url="https://example.com", headers={}, request=req, status=200, text="ok")
        download_result = MagicMock()
        download_result.response = resp
        engine.downloader_middleware_manager = MagicMock()
        engine.downloader_middleware_manager.process_request = AsyncMock(return_value=req)
        engine.downloader_middleware_manager.process_response = AsyncMock(return_value=None)
        engine._do_download = AsyncMock(return_value=download_result)

        result = await engine._fetch(req)
        assert result is None


class TestAioEngineDoDownload:
    """Test AioEngine._do_download exception handling."""

    @pytest.mark.asyncio
    async def test_do_download_success(self):
        engine = _make_engine()
        req = Request("https://example.com")
        engine.downloader.fetch = AsyncMock(return_value="result")
        result = await engine._do_download(req)
        assert result == "result"

    @pytest.mark.asyncio
    async def test_do_download_no_middleware_raises(self):
        """Without middleware manager, exceptions propagate."""
        engine = _make_engine()
        engine.downloader_middleware_manager = None
        req = Request("https://example.com")
        engine.downloader.fetch = AsyncMock(side_effect=RuntimeError("boom"))

        with pytest.raises(RuntimeError, match="boom"):
            await engine._do_download(req)

    @pytest.mark.asyncio
    async def test_do_download_middleware_handles_exception_none(self):
        """When middleware process_exception returns None, exception re-raises."""
        engine = _make_engine()
        req = Request("https://example.com")
        engine.downloader_middleware_manager = MagicMock()
        engine.downloader_middleware_manager.process_exception = AsyncMock(return_value=None)
        engine.downloader.fetch = AsyncMock(side_effect=RuntimeError("boom"))

        with pytest.raises(RuntimeError, match="boom"):
            await engine._do_download(req)

    @pytest.mark.asyncio
    async def test_do_download_middleware_returns_request(self):
        """When middleware returns Request, it's enqueued and None returned."""
        engine = _make_engine()
        req = Request("https://example.com")
        retry_req = Request("https://retry.com")
        engine.downloader_middleware_manager = MagicMock()
        engine.downloader_middleware_manager.process_exception = AsyncMock(return_value=retry_req)
        engine.downloader.fetch = AsyncMock(side_effect=RuntimeError("boom"))

        result = await engine._do_download(req)
        assert result is None
        engine.scheduler.put.assert_called_once_with(retry_req)

    @pytest.mark.asyncio
    async def test_do_download_middleware_returns_response(self):
        """When middleware returns Response, a DownloadResult wrapper is returned."""
        engine = _make_engine()
        req = Request("https://example.com")
        mock_resp = Response(url="https://example.com", headers={}, request=req, status=200, text="ok")
        engine.downloader_middleware_manager = MagicMock()
        engine.downloader_middleware_manager.process_exception = AsyncMock(return_value=mock_resp)
        engine.downloader.fetch = AsyncMock(side_effect=RuntimeError("boom"))

        result = await engine._do_download(req)
        assert result.response is mock_resp
        assert result.reason is None


class TestAioEngineHandleErrorResponse:
    """Test AioEngine._handle_error_response."""

    @pytest.mark.asyncio
    async def test_no_error_callback_returns_none(self):
        engine = _make_engine()
        req = Request("https://example.com")
        result = await engine._handle_error_response(req)
        assert result is None

    @pytest.mark.asyncio
    async def test_error_callback_coroutine(self):
        engine = _make_engine()

        async def err_cb(request):
            pass

        req = Request("https://example.com", error_callback=err_cb)
        await engine._handle_error_response(req)
        engine.spider.stats_collector.record_parse_fail.assert_called_once()


class TestAioEngineCloseSpider:
    """Test AioEngine.close_spider."""

    @pytest.mark.asyncio
    async def test_close_spider(self):
        engine = _make_engine()
        engine.downloader_middleware_manager = MagicMock()
        engine.downloader_middleware_manager.close = AsyncMock()
        engine.spider_middleware_manager = MagicMock()
        engine.spider_middleware_manager.close = AsyncMock()
        engine.downloader.close = AsyncMock()
        engine.processor.close = AsyncMock()

        await engine.close_spider()
        engine.downloader_middleware_manager.close.assert_called_once()
        engine.spider_middleware_manager.close.assert_called_once()
        engine.downloader.close.assert_called_once()
        engine.processor.close.assert_called_once()
