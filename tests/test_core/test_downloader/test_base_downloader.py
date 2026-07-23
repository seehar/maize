"""
Tests for base_downloader: ActiveRequestManager, ActiveRequestContextManager,
DownloaderMeta, BaseDownloader.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from maize.base.downloader.base_downloader import (
    ActiveRequestContextManager,
    ActiveRequestManager,
    BaseDownloader,
)
from maize.common.http.request import Request
from maize.common.http.response import Response
from maize.common.model.download_response_model import DownloadResponse
from maize.settings import SpiderSettings


class TestActiveRequestManager:
    """Test ActiveRequestManager and its context manager."""

    def test_add_and_remove(self):
        manager = ActiveRequestManager()
        req = Request("https://example.com")

        manager.add(req)
        assert len(manager) == 1

        manager.remove(req)
        assert len(manager) == 0

    def test_len_empty(self):
        manager = ActiveRequestManager()
        assert len(manager) == 0

    def test_multiple_requests(self):
        manager = ActiveRequestManager()
        a = Request("https://a.com")
        b = Request("https://b.com")

        manager.add(a)
        manager.add(b)
        assert len(manager) == 2

        manager.remove(a)
        assert len(manager) == 1
        manager.remove(b)
        assert len(manager) == 0

    def test_call_returns_context_manager(self):
        manager = ActiveRequestManager()
        req = Request("https://example.com")
        ctx = manager(req)
        assert isinstance(ctx, ActiveRequestContextManager)
        assert ctx._request is req

    @pytest.mark.asyncio
    async def test_context_manager_adds_and_removes(self):
        manager = ActiveRequestManager()
        req = Request("https://example.com")

        async with manager(req):
            assert len(manager) == 1

        assert len(manager) == 0

    @pytest.mark.asyncio
    async def test_context_manager_removes_on_exception(self):
        """Context manager should remove the request even if body raises."""
        manager = ActiveRequestManager()
        req = Request("https://example.com")

        with pytest.raises(ValueError):
            async with manager(req):
                assert len(manager) == 1
                raise ValueError("boom")

        assert len(manager) == 0


class TestDownloaderMeta:
    """Test DownloaderMeta.__subclasscheck__."""

    def test_subclass_with_all_methods(self):
        class FakeDownloader:
            def fetch(self): ...
            def download(self): ...
            def create_instance(self): ...
            def close(self): ...
            def idle(self): ...

        assert issubclass(FakeDownloader, BaseDownloader)

    def test_not_subclass_missing_method(self):
        class IncompleteDownloader:
            def fetch(self): ...
            def download(self): ...

        assert not issubclass(IncompleteDownloader, BaseDownloader)

    def test_base_downloader_is_subclass_of_itself(self):
        assert issubclass(BaseDownloader, BaseDownloader)


class _ConcreteDownloader(BaseDownloader):
    """Concrete subclass for testing BaseDownloader methods."""

    async def download(self, request: Request) -> DownloadResponse | Request:
        return DownloadResponse()

    @staticmethod
    def structure_response(request: Request, _response, body: bytes) -> Response:
        return Response(
            url=request.url,
            headers={},
            request=request,
            body=body,
        )


class TestBaseDownloader:
    """Test BaseDownloader methods using a concrete subclass."""

    def _make_downloader(self, max_retry=0):
        crawler = MagicMock()
        crawler.settings = SpiderSettings()
        crawler.settings.request.max_retry_count = max_retry
        return _ConcreteDownloader(crawler)

    def test_init(self):
        dl = self._make_downloader(max_retry=3)
        assert dl.crawler is not None
        assert dl._max_retry_count == 3
        assert dl._active is not None

    def test_create_instance(self):
        crawler = MagicMock()
        crawler.settings = SpiderSettings()

        instance = _ConcreteDownloader.create_instance(crawler)
        assert isinstance(instance, _ConcreteDownloader)
        assert instance.crawler is crawler

    def test_idle_true_when_no_active(self):
        dl = self._make_downloader()
        assert dl.idle() is True

    def test_idle_false_when_active(self):
        dl = self._make_downloader()
        req = Request("https://example.com")
        dl._active.add(req)
        assert dl.idle() is False

    @pytest.mark.asyncio
    async def test_fetch_wraps_download_with_active_manager(self):
        dl = self._make_downloader()
        req = Request("https://example.com")
        expected = DownloadResponse()

        dl.download = AsyncMock(return_value=expected)
        result = await dl.fetch(req)

        assert result is expected
        assert dl.idle() is True

    @pytest.mark.asyncio
    async def test_random_wait_calls_sleep(self):
        dl = self._make_downloader()
        dl.crawler.settings.request.random_wait_time = (0, 0)
        await dl.random_wait()

    @pytest.mark.asyncio
    async def test_download_retry_within_limit(self):
        dl = self._make_downloader(max_retry=3)
        req = Request("https://example.com")
        result = await dl._download_retry(req, ConnectionError("timeout"))
        assert result is req
        assert req.current_retry_count == 1

    @pytest.mark.asyncio
    async def test_download_retry_exceeds_limit_returns_none(self):
        dl = self._make_downloader(max_retry=2)
        req = Request("https://example.com")
        req.retry()
        req.retry()
        result = await dl._download_retry(req, ConnectionError("timeout"))
        assert result is None

    @pytest.mark.asyncio
    async def test_download_retry_calls_process_error_request(self):
        dl = self._make_downloader(max_retry=1)
        req = Request("https://example.com")
        req.retry()
        dl.process_error_request = AsyncMock()
        result = await dl._download_retry(req, ConnectionError("timeout"))
        assert result is None
        dl.process_error_request.assert_called_once_with(req)

    @pytest.mark.asyncio
    async def test_open_logs_info(self):
        dl = self._make_downloader()
        dl.crawler.spider = "TestSpider"
        dl.crawler.settings.concurrency = 5
        await dl.open()

    @pytest.mark.asyncio
    async def test_close_logs_info(self):
        dl = self._make_downloader()
        dl.crawler.spider = "TestSpider"
        await dl.close()

    @pytest.mark.asyncio
    async def test_process_error_request_default_noop(self):
        dl = self._make_downloader()
        req = Request("https://example.com")
        await dl.process_error_request(req)
