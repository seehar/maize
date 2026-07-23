"""
Tests for AioHttpDownloader structure_response, open, close, send_request.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from aiohttp import BasicAuth, ClientResponse, ClientSession

from maize.aio.classic.downloader.aiohttp_downloader import AioHttpDownloader
from maize.common.constant.request_constant import Method
from maize.common.http.request import Request
from maize.settings import SpiderSettings


def _make_crawler(use_session=True, proxy_url=None, proxy_user=None, proxy_pass=None):
    crawler = MagicMock()
    crawler.settings = SpiderSettings()
    crawler.settings.request.use_session = use_session
    crawler.settings.proxy.proxy_url = proxy_url or ""
    crawler.settings.proxy.proxy_username = proxy_user or ""
    crawler.settings.proxy.proxy_password = proxy_pass or ""
    crawler.spider = "TestSpider"
    return crawler


class TestAioHttpDownloaderStructureResponse:
    """Test the static structure_response method."""

    def test_structure_response_builds_response(self):
        req = Request("https://example.com", method=Method.GET)
        mock_resp = MagicMock(spec=ClientResponse)
        mock_resp.headers = {"Content-Type": "text/html"}
        mock_resp.status = 200

        response = AioHttpDownloader.structure_response(req, mock_resp, b"<html></html>")

        assert response.url == "https://example.com"
        assert response.status == 200
        assert response.body == b"<html></html>"
        assert response.headers == {"Content-Type": "text/html"}
        assert response.request is req
        assert response.source_response is mock_resp


class TestAioHttpDownloaderInit:
    """Test AioHttpDownloader.__init__ and open()."""

    def test_init_defaults(self):
        crawler = _make_crawler()
        dl = AioHttpDownloader(crawler)
        assert dl.session is None
        assert dl.trace_config is None
        assert dl.proxy_tunnel is None
        assert dl.proxy_auth is None

    @pytest.mark.asyncio
    async def test_open_sets_proxy_and_auth(self):
        crawler = _make_crawler(proxy_url="http://proxy:8080", proxy_user="user", proxy_pass="pass")
        dl = AioHttpDownloader(crawler)
        await dl.open()
        assert dl.proxy_tunnel == "http://proxy:8080"
        assert isinstance(dl.proxy_auth, BasicAuth)
        await dl.close()

    @pytest.mark.asyncio
    async def test_open_without_session(self):
        crawler = _make_crawler(use_session=False)
        dl = AioHttpDownloader(crawler)
        await dl.open()
        assert dl.session is None
        await dl.close()


class TestAioHttpDownloaderClose:
    """Test AioHttpDownloader.close."""

    @pytest.mark.asyncio
    async def test_close_cleans_up(self):
        crawler = _make_crawler(use_session=True)
        dl = AioHttpDownloader(crawler)
        await dl.open()
        session = dl.session
        connector = dl.connector
        await dl.close()
        assert session.closed
        assert connector.closed

    @pytest.mark.asyncio
    async def test_close_when_not_opened(self):
        """close() should not raise if nothing was opened."""
        crawler = _make_crawler()
        dl = AioHttpDownloader(crawler)
        await dl.close()


class TestAioHttpDownloaderSendRequest:
    """Test AioHttpDownloader.send_request."""

    @pytest.mark.asyncio
    async def test_send_request_with_request_proxy(self):
        crawler = _make_crawler()
        dl = AioHttpDownloader(crawler)
        req = Request(
            "https://example.com",
            method=Method.POST,
            proxy="http://req-proxy:8080",
            proxy_username="ruser",
            proxy_password="rpass",
        )

        session = MagicMock(spec=ClientSession)
        session.request = AsyncMock(return_value=MagicMock(spec=ClientResponse))

        await dl.send_request(session, req)
        call_kwargs = session.request.call_args
        assert call_kwargs.kwargs["proxy"] == "http://req-proxy:8080"
        assert isinstance(call_kwargs.kwargs["proxy_auth"], BasicAuth)

    @pytest.mark.asyncio
    async def test_send_request_falls_back_to_downloader_proxy(self):
        crawler = _make_crawler(proxy_url="http://dl-proxy:8080", proxy_user="duser", proxy_pass="dpass")
        dl = AioHttpDownloader(crawler)
        await dl.open()
        req = Request("https://example.com", method=Method.GET)

        session = MagicMock(spec=ClientSession)
        session.request = AsyncMock(return_value=MagicMock(spec=ClientResponse))

        await dl.send_request(session, req)
        call_kwargs = session.request.call_args
        assert call_kwargs.kwargs["proxy"] == "http://dl-proxy:8080"
        assert isinstance(call_kwargs.kwargs["proxy_auth"], BasicAuth)
        await dl.close()

    @pytest.mark.asyncio
    async def test_send_request_passes_all_params(self):
        crawler = _make_crawler()
        dl = AioHttpDownloader(crawler)
        req = Request(
            "https://example.com",
            method=Method.POST,
            params={"page": 1},
            data={"q": "test"},
            json={"key": "value"},
            headers={"X-Test": "1"},
            cookies={"session": "abc"},
        )

        session = MagicMock(spec=ClientSession)
        session.request = AsyncMock(return_value=MagicMock(spec=ClientResponse))

        await dl.send_request(session, req)
        call_kwargs = session.request.call_args
        assert call_kwargs.kwargs["method"] == "POST"
        assert call_kwargs.kwargs["url"] == "https://example.com"
        assert call_kwargs.kwargs["params"] == {"page": 1}
        assert call_kwargs.kwargs["data"] == {"q": "test"}
        assert call_kwargs.kwargs["json"] == {"key": "value"}
        assert call_kwargs.kwargs["headers"] == {"X-Test": "1"}
        assert call_kwargs.kwargs["cookies"] == {"session": "abc"}
