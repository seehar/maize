"""同步 Lite 爬虫功能测试。

使用本地 mock HTTP server 验证 SyncLiteSpider 端到端流程：
- start_requests → fetch → parse → process_item
- 并发、重试、去重、深度控制
"""

import threading
from collections.abc import Generator
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from maize.common.http import Request, Response
from maize.common.items import Item
from maize.common.items.field import Field
from maize.sync.lite import SyncLiteSpider


class _MockHandler(BaseHTTPRequestHandler):
    """简单的 mock HTTP handler。"""

    def do_GET(self):
        if self.path == "/ok":
            body = b'{"status": "ok"}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/error":
            self.send_response(500)
            self.end_headers()
        elif self.path == "/links":
            body = b'<html><a href="/ok">link1</a><a href="/ok">link2</a></html>'
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass


@pytest.fixture(scope="module")
def mock_server():
    """启动本地 mock HTTP server。"""
    server = HTTPServer(("127.0.0.1", 0), _MockHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    server.shutdown()


class TestSyncLiteSpiderBasic:
    """基础端到端测试。"""

    def test_simple_fetch(self, mock_server):
        """测试简单抓取流程。"""
        results: list[str] = []

        class MySpider(SyncLiteSpider):
            def start_requests(self) -> Generator[Request, None, None]:
                yield Request(url=f"{mock_server}/ok")

            def parse(self, response: Response):
                results.append(f"{response.status}:{response.url}")

        spider = MySpider(concurrency=1, retry=1)
        spider.run()

        assert len(results) == 1
        assert "200:" in results[0]
        assert spider._client is None  # close 后 client 已关闭

    def test_concurrent_fetch(self, mock_server):
        """测试多 URL 并发抓取。"""
        fetched_urls: list[str] = []

        class MySpider(SyncLiteSpider):
            def start_requests(self) -> Generator[Request, None, None]:
                for i in range(5):
                    yield Request(url=f"{mock_server}/ok", meta={"dont_filter": True, "i": i})

            def parse(self, response: Response):
                fetched_urls.append(response.url)

        spider = MySpider(concurrency=3)
        spider.run()

        assert len(fetched_urls) == 5

    def test_retry_on_500(self, mock_server):
        """测试 500 错误重试。"""
        attempt_count = 0

        class MySpider(SyncLiteSpider):
            def start_requests(self) -> Generator[Request, None, None]:
                yield Request(url=f"{mock_server}/error")

            def parse(self, response: Response):
                nonlocal attempt_count
                attempt_count += 1

        spider = MySpider(concurrency=1, retry=2)
        spider.run()

        # retry=2 意味着总共尝试 2 次
        # 500 会一直重试到用尽次数，最后一次仍 500，parse 会被调用 1 次
        assert attempt_count == 1


class TestSyncLiteSpiderFollowLinks:
    """链接跟进测试。"""

    def test_follow_links(self, mock_server):
        """测试 parse 中 yield Request 自动跟进。"""
        visited: list[str] = []

        class MySpider(SyncLiteSpider):
            def start_requests(self) -> Generator[Request, None, None]:
                yield Request(url=f"{mock_server}/links")

            def parse(self, response: Response):
                visited.append(response.url)
                # 从 /links 页面跟进 /ok 链接
                if "links" in response.url:
                    yield Request(url=f"{mock_server}/ok")

        spider = MySpider(concurrency=1, retry=1)
        spider.run()

        # /links + /ok（去重后只有 1 个 /ok）
        assert len(visited) == 2
        assert any("links" in u for u in visited)
        assert any("/ok" in u for u in visited)

    def test_max_depth(self, mock_server):
        """测试最大深度控制。"""
        visited: list[str] = []

        class MySpider(SyncLiteSpider):
            @property
            def max_depth(self) -> int:
                return 0  # 不限深度

            def start_requests(self) -> Generator[Request, None, None]:
                yield Request(url=f"{mock_server}/links")

            def parse(self, response: Response):
                visited.append(response.url)
                yield Request(url=f"{mock_server}/ok")

        spider = MySpider(concurrency=1, retry=1)
        spider.run()

        assert len(visited) >= 2

    def test_dedup(self, mock_server):
        """测试请求去重。"""
        visited: list[str] = []

        class MySpider(SyncLiteSpider):
            def start_requests(self) -> Generator[Request, None, None]:
                # 同一个 URL 产出 3 次，去重后只应抓 1 次
                yield Request(url=f"{mock_server}/ok")
                yield Request(url=f"{mock_server}/ok")
                yield Request(url=f"{mock_server}/ok")

            def parse(self, response: Response):
                visited.append(response.url)

        spider = MySpider(concurrency=1, retry=1)
        spider.run()

        assert len(visited) == 1


class TestSyncLiteSpiderItem:
    """Item 收集测试。"""

    def test_item_collection(self, mock_server):
        """测试 parse 中 yield Item 自动收集。"""

        class MyItem(Item):
            url: str = Field()
            status: int = Field()

        collected: list[MyItem] = []

        class MySpider(SyncLiteSpider):
            def start_requests(self) -> Generator[Request, None, None]:
                yield Request(url=f"{mock_server}/ok")

            def parse(self, response: Response):
                yield MyItem(url=response.url, status=response.status)

            def process_item(self, item: Item) -> None:
                collected.append(item)

        spider = MySpider(concurrency=1, retry=1)
        spider.run()

        assert len(collected) == 1
        assert collected[0].status == 200
