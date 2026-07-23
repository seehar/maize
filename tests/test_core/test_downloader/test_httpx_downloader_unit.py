"""
Tests for HTTPXDownloader structure_response, _get_proxy, open, close.
"""

from unittest.mock import MagicMock

import httpx
import pytest

from maize.aio.classic.downloader.httpx_downloader import HTTPXDownloader
from maize.common.constant.request_constant import Method
from maize.common.http.request import Request
from maize.settings import SpiderSettings


def _make_crawler(proxy_url=None, proxy_user=None, proxy_pass=None):
    crawler = MagicMock()
    crawler.settings = SpiderSettings()
    crawler.settings.proxy.proxy_url = proxy_url or ""
    crawler.settings.proxy.proxy_username = proxy_user or ""
    crawler.settings.proxy.proxy_password = proxy_pass or ""
    crawler.spider = "TestSpider"
    return crawler


class TestHTTPXDownloaderStructureResponse:
    """Test the static structure_response method."""

    def test_structure_response_builds_response(self):
        req = Request("https://example.com", method=Method.GET)
        mock_resp = MagicMock(spec=httpx.Response)
        mock_resp.headers = {"Content-Type": "text/html"}
        mock_resp.status_code = 200

        response = HTTPXDownloader.structure_response(req, mock_resp, b"<html></html>")

        assert response.url == "https://example.com"
        assert response.status == 200
        assert response.body == b"<html></html>"
        assert response.headers == {"Content-Type": "text/html"}
        assert response.request is req
        assert response.source_response is mock_resp


class TestHTTPXDownloaderInit:
    """Test HTTPXDownloader.__init__."""

    def test_init_defaults(self):
        crawler = _make_crawler()
        dl = HTTPXDownloader(crawler)
        assert dl._timeout is None
        assert dl.httpx_proxy is None


class TestHTTPXDownloaderOpen:
    """Test HTTPXDownloader.open."""

    @pytest.mark.asyncio
    async def test_open_sets_timeout(self):
        crawler = _make_crawler()
        dl = HTTPXDownloader(crawler)
        await dl.open()
        assert dl._timeout is not None
        await dl.close()

    @pytest.mark.asyncio
    async def test_open_with_proxy_auth(self):
        crawler = _make_crawler(proxy_url="proxy:8080", proxy_user="user", proxy_pass="pass")
        dl = HTTPXDownloader(crawler)
        await dl.open()
        assert dl.httpx_proxy is not None
        await dl.close()

    @pytest.mark.asyncio
    async def test_open_with_proxy_no_auth(self):
        crawler = _make_crawler(proxy_url="proxy:8080")
        dl = HTTPXDownloader(crawler)
        await dl.open()
        assert dl.httpx_proxy is not None
        await dl.close()

    @pytest.mark.asyncio
    async def test_open_without_proxy(self):
        crawler = _make_crawler()
        dl = HTTPXDownloader(crawler)
        await dl.open()
        assert dl.httpx_proxy is None
        await dl.close()


class TestHTTPXDownloaderGetProxy:
    """Test HTTPXDownloader._get_proxy."""

    def test_get_proxy_no_request_proxy_uses_downloader_proxy(self):
        crawler = _make_crawler(proxy_url="proxy:8080", proxy_user="u", proxy_pass="p")
        dl = HTTPXDownloader(crawler)
        dl.httpx_proxy = httpx.Proxy(url="http://dl-proxy:8080")
        req = Request("https://example.com")
        result = dl._get_proxy(req)
        assert result is dl.httpx_proxy

    def test_get_proxy_request_proxy_without_auth(self):
        crawler = _make_crawler()
        dl = HTTPXDownloader(crawler)
        req = Request("https://example.com", proxy="req-proxy:9090")
        result = dl._get_proxy(req)
        assert isinstance(result, httpx.Proxy)

    def test_get_proxy_request_proxy_with_auth(self):
        crawler = _make_crawler()
        dl = HTTPXDownloader(crawler)
        req = Request(
            "https://example.com",
            proxy="req-proxy:9090",
            proxy_username="ru",
            proxy_password="rp",
        )
        result = dl._get_proxy(req)
        assert isinstance(result, httpx.Proxy)

    def test_get_proxy_no_proxy_returns_none(self):
        crawler = _make_crawler()
        dl = HTTPXDownloader(crawler)
        req = Request("https://example.com")
        result = dl._get_proxy(req)
        assert result is None
