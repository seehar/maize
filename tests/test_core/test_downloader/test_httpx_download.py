"""
Tests for HTTPXDownloader.download method.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from maize.aio.classic.downloader.httpx_downloader import HTTPXDownloader
from maize.common.constant.request_constant import Method
from maize.common.http.request import Request
from maize.common.model.download_response_model import DownloadResponse
from maize.settings import SpiderSettings


def _make_crawler(max_retry=0):
    crawler = MagicMock()
    crawler.settings = SpiderSettings()
    crawler.settings.request.max_retry_count = max_retry
    crawler.spider = "TestSpider"
    return crawler


def _make_mock_httpx_response(status=200, body=b"<html>ok</html>"):
    resp = MagicMock(spec=httpx.Response)
    resp.headers = {"Content-Type": "text/html"}
    resp.status_code = status
    resp.aread = AsyncMock(return_value=body)
    return resp


class TestHTTPXDownloaderDownload:
    """Test HTTPXDownloader.download."""

    @pytest.mark.asyncio
    async def test_download_success(self):
        crawler = _make_crawler()
        dl = HTTPXDownloader(crawler)
        await dl.open()

        mock_resp = _make_mock_httpx_response(200, b"httpx-ok")

        mock_client = MagicMock()
        mock_client.request = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("maize.aio.classic.downloader.httpx_downloader.httpx.AsyncClient", return_value=mock_client):
            req = Request("https://example.com", method=Method.GET)
            result = await dl.download(req)

        assert isinstance(result, DownloadResponse)
        assert result.response.status == 200
        assert result.response.body == b"httpx-ok"
        await dl.close()

    @pytest.mark.asyncio
    async def test_download_exception_returns_download_response(self):
        crawler = _make_crawler(max_retry=0)
        dl = HTTPXDownloader(crawler)
        await dl.open()

        mock_client = MagicMock()
        mock_client.request = AsyncMock(side_effect=httpx.ConnectError("refused"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("maize.aio.classic.downloader.httpx_downloader.httpx.AsyncClient", return_value=mock_client):
            req = Request("https://example.com", method=Method.GET)
            result = await dl.download(req)

        assert isinstance(result, DownloadResponse)
        assert result.response is None
        assert "refused" in result.reason
        await dl.close()

    @pytest.mark.asyncio
    async def test_download_with_retry(self):
        crawler = _make_crawler(max_retry=1)
        dl = HTTPXDownloader(crawler)
        await dl.open()

        mock_client = MagicMock()
        mock_client.request = AsyncMock(side_effect=httpx.ConnectError("refused"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("maize.aio.classic.downloader.httpx_downloader.httpx.AsyncClient", return_value=mock_client):
            req = Request("https://example.com", method=Method.GET)
            result = await dl.download(req)

        # With max_retry=1, first failure returns Request for retry
        assert isinstance(result, Request)
        assert result.current_retry_count == 1
        await dl.close()
