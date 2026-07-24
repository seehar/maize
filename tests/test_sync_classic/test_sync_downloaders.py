"""同步下载器和优先级队列单元测试。

覆盖 SyncHttpxDownloader 的代理/临时 client 分支。
覆盖 SyncRequestsDownloader 的全流程。
覆盖 SyncSpiderPriorityQueue 的 get_by_priority。
"""

import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from unittest.mock import patch

import httpx
import pytest

from maize import Method, Request, SpiderSettings
from maize.common.model.download_response_model import DownloadResponse
from maize.sync.classic.downloader import sync_requests_downloader as srd
from maize.sync.classic.downloader.sync_httpx_downloader import SyncHttpxDownloader
from maize.sync.classic.downloader.sync_requests_downloader import SyncRequestsDownloader
from maize.utils.log_util import set_spider_settings
from maize.utils.sync_priority_queue import SyncSpiderPriorityQueue

try:
    import requests as req_lib
except ImportError:
    req_lib = None


class _MockHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = b'{"ok": true}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        body = b'{"posted": true}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass


@pytest.fixture(scope="module")
def mock_server():
    server = HTTPServer(("127.0.0.1", 0), _MockHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    server.shutdown()


class _FakeCrawler:
    def __init__(self, settings=None):
        self.settings = settings or SpiderSettings()
        self.spider = None


@pytest.fixture(autouse=True)
def _setup():
    set_spider_settings(SpiderSettings())


class TestSyncHttpxDownloader:
    def test_basic_get(self, mock_server):
        crawler = _FakeCrawler()
        dl = SyncHttpxDownloader(crawler)
        dl.open()
        try:
            req = Request(url=f"{mock_server}/ok")
            result = dl.download(req)
            assert isinstance(result, DownloadResponse)
            assert result.response is not None
            assert result.response.status == 200
        finally:
            dl.close()

    def test_post_with_json(self, mock_server):
        crawler = _FakeCrawler()
        dl = SyncHttpxDownloader(crawler)
        dl.open()
        try:
            req = Request(url=f"{mock_server}/ok", method=Method.POST, json={"key": "value"})
            result = dl.download(req)
            assert isinstance(result, DownloadResponse)
            assert result.response.status == 200
        finally:
            dl.close()

    def test_per_request_proxy_creates_temp_client(self, mock_server):
        """per-request proxy 与全局不同时创建临时 client。"""
        crawler = _FakeCrawler()
        dl = SyncHttpxDownloader(crawler)
        dl.open()
        try:
            req = Request(url=f"{mock_server}/ok", proxy="127.0.0.1:9999")
            # 会尝试通过不可达代理连接，触发异常 → retry → DownloadResponse(reason=...)
            result = dl.download(req)
            assert isinstance(result, DownloadResponse)
        finally:
            dl.close()

    def test_max_redirects_creates_temp_client(self, mock_server):
        """max_redirects != 20 时创建临时 client。"""
        crawler = _FakeCrawler()
        dl = SyncHttpxDownloader(crawler)
        dl.open()
        try:
            req = Request(url=f"{mock_server}/ok", max_redirects=5)
            result = dl.download(req)
            assert isinstance(result, DownloadResponse)
            assert result.response is not None
        finally:
            dl.close()

    def test_download_failure_returns_reason(self):
        crawler = _FakeCrawler()
        dl = SyncHttpxDownloader(crawler)
        dl.open()
        try:
            req = Request(url="http://127.0.0.1:1/unreachable")
            # mock 网络层抛连接异常，避免本机代理拦截 127.0.0.1:1 返回 502 干扰
            with patch.object(dl._client, "request", side_effect=httpx.ConnectError("connection refused")):
                result = dl.download(req)
            assert isinstance(result, DownloadResponse)
            assert result.response is None
            assert result.reason is not None
        finally:
            dl.close()

    def test_download_not_initialized_raises(self):
        crawler = _FakeCrawler()
        dl = SyncHttpxDownloader(crawler)
        req = Request(url="http://example.com")
        with pytest.raises(RuntimeError, match="Client not initialized"):
            dl.download(req)

    def test_global_proxy_config(self):
        """全局 proxy 配置时 open() 创建带 proxy 的 client。"""
        settings = SpiderSettings()
        settings.proxy.proxy_url = "127.0.0.1:9999"
        crawler = _FakeCrawler(settings)
        dl = SyncHttpxDownloader(crawler)
        dl.open()
        assert dl.httpx_proxy is not None
        dl.close()

    def test_global_proxy_with_auth(self):
        settings = SpiderSettings()
        settings.proxy.proxy_url = "127.0.0.1:9999"
        settings.proxy.proxy_username = "user"
        settings.proxy.proxy_password = "pass"
        crawler = _FakeCrawler(settings)
        dl = SyncHttpxDownloader(crawler)
        dl.open()
        assert dl.httpx_proxy is not None
        dl.close()

    def test_structure_response(self, mock_server):
        req = Request(url=f"{mock_server}/ok")
        raw_resp = httpx.Response(200, headers={"X-Test": "1"}, content=b"body")
        structured = SyncHttpxDownloader.structure_response(req, raw_resp, b"body")
        assert structured.status == 200
        assert structured.body == b"body"
        assert structured.headers["x-test"] == "1"

    def test_idle_always_true(self):
        crawler = _FakeCrawler()
        dl = SyncHttpxDownloader(crawler)
        assert dl.idle() is True


class TestSyncRequestsDownloader:
    def test_basic_get(self, mock_server):
        pytest.importorskip("requests")

        crawler = _FakeCrawler()
        dl = SyncRequestsDownloader(crawler)
        dl.open()
        try:
            req = Request(url=f"{mock_server}/ok")
            result = dl.download(req)
            assert isinstance(result, DownloadResponse)
            assert result.response is not None
            assert result.response.status == 200
        finally:
            dl.close()

    def test_post_with_data(self, mock_server):
        pytest.importorskip("requests")

        crawler = _FakeCrawler()
        dl = SyncRequestsDownloader(crawler)
        dl.open()
        try:
            req = Request(url=f"{mock_server}/ok", method=Method.POST, data={"key": "value"})
            result = dl.download(req)
            assert isinstance(result, DownloadResponse)
            assert result.response.status == 200
        finally:
            dl.close()

    def test_download_failure(self):
        pytest.importorskip("requests")

        crawler = _FakeCrawler()
        dl = SyncRequestsDownloader(crawler)
        dl.open()
        try:
            req = Request(url="http://127.0.0.1:1/unreachable")
            result = dl.download(req)
            assert isinstance(result, DownloadResponse)
            assert result.response is None
            assert result.reason is not None
        finally:
            dl.close()

    def test_per_request_proxy(self, mock_server):
        pytest.importorskip("requests")

        crawler = _FakeCrawler()
        dl = SyncRequestsDownloader(crawler)
        dl.open()
        try:
            req = Request(url=f"{mock_server}/ok", proxy="127.0.0.1:9999")
            result = dl.download(req)
            assert isinstance(result, DownloadResponse)
        finally:
            dl.close()

    def test_global_proxy_config(self):
        pytest.importorskip("requests")

        settings = SpiderSettings()
        settings.proxy.proxy_url = "127.0.0.1:9999"
        crawler = _FakeCrawler(settings)
        dl = SyncRequestsDownloader(crawler)
        dl.open()
        assert dl._proxies is not None
        dl.close()

    def test_structure_response(self):
        pytest.importorskip("requests")

        request = Request(url="http://example.com")
        raw_resp = req_lib.Response()
        raw_resp.status_code = 200
        raw_resp.headers["X-Test"] = "1"
        raw_resp._content = b"body"
        structured = SyncRequestsDownloader.structure_response(request, raw_resp, b"body")
        assert structured.status == 200
        assert structured.body == b"body"

    def test_not_installed_raises(self):
        """requests 未安装时 open() 应抛出 ImportError。"""

        original = srd.requests
        try:
            srd.requests = None
            crawler = _FakeCrawler()
            dl = srd.SyncRequestsDownloader(crawler)
            with pytest.raises(ImportError, match="requests is not installed"):
                dl.open()
        finally:
            srd.requests = original


class TestSyncSpiderPriorityQueue:
    def test_put_get_ordering(self):
        q = SyncSpiderPriorityQueue()
        q.put(Request(url="http://low.com", priority=10))
        q.put(Request(url="http://high.com", priority=1))
        q.put(Request(url="http://mid.com", priority=5))

        first = q.get()
        assert first.url == "http://high.com"
        second = q.get()
        assert second.url == "http://mid.com"
        third = q.get()
        assert third.url == "http://low.com"

    def test_get_empty_returns_none(self):
        q = SyncSpiderPriorityQueue()
        assert q.get(timeout=0.01) is None

    def test_len_and_empty(self):
        q = SyncSpiderPriorityQueue()
        assert len(q) == 0
        assert q.empty() is True
        q.put(Request(url="http://a.com"))
        assert len(q) == 1
        assert q.empty() is False
        assert q.qsize() == 1

    def test_get_by_priority_match(self):
        q = SyncSpiderPriorityQueue()
        q.put(Request(url="http://a.com", priority=5))
        result = q.get_by_priority(3)
        assert result is not None
        assert result.url == "http://a.com"

    def test_get_by_priority_no_match_puts_back(self):
        q = SyncSpiderPriorityQueue()
        q.put(Request(url="http://a.com", priority=1))
        result = q.get_by_priority(5)
        assert result is None
        assert len(q) == 1  # 放回了

    def test_get_by_priority_empty(self):
        q = SyncSpiderPriorityQueue()
        result = q.get_by_priority(1, timeout=0.01)
        assert result is None

    def test_fifo_within_same_priority(self):
        q = SyncSpiderPriorityQueue()
        q.put(Request(url="http://first.com", priority=5))
        q.put(Request(url="http://second.com", priority=5))
        first = q.get()
        second = q.get()
        assert first.url == "http://first.com"
        assert second.url == "http://second.com"
