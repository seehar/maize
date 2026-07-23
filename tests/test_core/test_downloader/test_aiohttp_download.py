"""
Tests for AioHttpDownloader.download method (session and non-session paths).
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from aiohttp import ClientResponse, ClientSession

from maize.aio.classic.downloader.aiohttp_downloader import AioHttpDownloader
from maize.common.constant.request_constant import Method
from maize.common.http.request import Request
from maize.common.model.download_response_model import DownloadResponse
from maize.settings import SpiderSettings


def _make_crawler(use_session=True, max_retry=0):
    crawler = MagicMock()
    crawler.settings = SpiderSettings()
    crawler.settings.request.use_session = use_session
    crawler.settings.request.max_retry_count = max_retry
    crawler.spider = "TestSpider"
    return crawler


def _make_mock_response(status=200, body=b"<html>ok</html>"):
    resp = MagicMock(spec=ClientResponse)
    resp.headers = {"Content-Type": "text/html"}
    resp.status = status
    resp.content = MagicMock()
    resp.content.read = AsyncMock(return_value=body)
    return resp


class TestAioHttpDownloaderDownloadSession:
    """Test AioHttpDownloader.download with session mode."""

    @pytest.mark.asyncio
    async def test_download_session_success(self):
        crawler = _make_crawler(use_session=True)
        dl = AioHttpDownloader(crawler)
        await dl.open()

        mock_resp = _make_mock_response(200, b"hello")
        dl.send_request = AsyncMock(return_value=mock_resp)

        req = Request("https://example.com", method=Method.GET)
        result = await dl.download(req)

        assert isinstance(result, DownloadResponse)
        assert result.response.status == 200
        assert result.response.body == b"hello"
        await dl.close()

    @pytest.mark.asyncio
    async def test_download_session_exception_returns_download_response(self):
        crawler = _make_crawler(use_session=True, max_retry=1)
        dl = AioHttpDownloader(crawler)
        await dl.open()

        dl.send_request = AsyncMock(side_effect=RuntimeError("timeout"))

        req = Request("https://example.com", method=Method.GET)
        result = await dl.download(req)

        # First failure -> retry returns the Request
        assert isinstance(result, Request)
        assert result.current_retry_count == 1
        await dl.close()

    @pytest.mark.asyncio
    async def test_download_session_exception_max_retry_returns_download_response(self):
        crawler = _make_crawler(use_session=True, max_retry=0)
        dl = AioHttpDownloader(crawler)
        await dl.open()

        dl.send_request = AsyncMock(side_effect=RuntimeError("timeout"))

        req = Request("https://example.com", method=Method.GET)
        result = await dl.download(req)

        assert isinstance(result, DownloadResponse)
        assert result.response is None
        assert "timeout" in result.reason
        await dl.close()


class TestAioHttpDownloaderDownloadNoSession:
    """Test AioHttpDownloader.download without session (creates per-request session)."""

    @pytest.mark.asyncio
    async def test_download_non_session_success(self):
        crawler = _make_crawler(use_session=False)
        dl = AioHttpDownloader(crawler)
        await dl.open()

        mock_resp = _make_mock_response(200, b"no-session")

        # Mock ClientSession context manager
        mock_session = MagicMock(spec=ClientSession)
        mock_session.request = AsyncMock(return_value=mock_resp)

        with patch("maize.aio.classic.downloader.aiohttp_downloader.ClientSession") as mock_cs:
            mock_cs.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_cs.return_value.__aexit__ = AsyncMock(return_value=None)

            req = Request("https://example.com", method=Method.GET)
            result = await dl.download(req)

        assert isinstance(result, DownloadResponse)
        assert result.response.status == 200
        assert result.response.body == b"no-session"
        await dl.close()


# Import patch at top
from unittest.mock import patch  # noqa: E402
