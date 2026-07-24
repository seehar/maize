"""同步 Lite 爬虫补充测试。

覆盖 SyncLiteCrawler 和 SyncLiteSpider 的未覆盖分支：
- per_domain_concurrency 限流
- graceful shutdown（stop_event）
- feed_start_requests 异常
- fetch 临时 client（per-request proxy / max_redirects）
- should_retry 自定义
- process_item 异常
- callback 路由
- stats 属性
"""

import threading
import time
from collections.abc import Generator
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from maize.common.http import Request, Response
from maize.common.items import Item
from maize.common.items.field import Field
from maize.sync.lite import SyncLiteSpider
from maize.sync.lite.crawler.sync_lite_crawler import SyncLiteCrawler


class _MockHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/ok"):
            body = b'{"status": "ok"}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path.startswith("/error"):
            self.send_response(500)
            self.end_headers()
        elif self.path.startswith("/slow"):
            time.sleep(0.3)
            body = b"slow"
            self.send_response(200)
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
    server = HTTPServer(("127.0.0.1", 0), _MockHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    server.shutdown()


class _TestItem(Item):
    url: str = Field()


class TestSyncLiteCrawlerPerDomain:
    def test_per_domain_concurrency_serializes(self, mock_server):
        """per_domain_concurrency=1 时同域名请求串行。"""
        timestamps: list[float] = []

        class MySpider(SyncLiteSpider):
            @property
            def per_domain_concurrency(self) -> int:
                return 1

            @property
            def dedup(self) -> bool:
                return False

            def start_requests(self) -> Generator[Request, None, None]:
                for i in range(3):
                    yield Request(url=f"{mock_server}/slow?n={i}")

            def parse(self, response: Response):
                timestamps.append(time.monotonic())

        spider = MySpider(concurrency=3)
        crawler = SyncLiteCrawler(spider)
        crawler.crawl()
        assert len(timestamps) == 3
        # 串行：相邻请求间隔应 >= 0.2s（slow 路由 sleep 0.3s）
        for i in range(1, len(timestamps)):
            assert timestamps[i] - timestamps[i - 1] >= 0.2


class TestSyncLiteCrawlerGracefulShutdown:
    def test_stop_event_stops_crawl(self, mock_server):
        """stop_event 触发后爬虫停止接受新请求。"""
        fetched: list[str] = []

        class MySpider(SyncLiteSpider):
            @property
            def dedup(self) -> bool:
                return False

            def start_requests(self) -> Generator[Request, None, None]:
                for i in range(10):
                    yield Request(url=f"{mock_server}/slow?n={i}")

            def parse(self, response: Response):
                fetched.append(response.url)

        spider = MySpider(concurrency=1)
        crawler = SyncLiteCrawler(spider)

        def stop_after_delay():
            time.sleep(0.5)
            crawler._stop_event.set()

        stopper = threading.Thread(target=stop_after_delay, daemon=True)
        stopper.start()
        crawler.crawl()
        # 不应完成全部 10 个请求
        assert len(fetched) < 10


class TestSyncLiteCrawlerFeedError:
    def test_start_requests_exception(self, mock_server):
        """start_requests 抛异常时爬虫正常退出。"""
        fetched: list[str] = []

        class MySpider(SyncLiteSpider):
            def start_requests(self) -> Generator[Request, None, None]:
                yield Request(url=f"{mock_server}/ok")
                raise ValueError("feed error")

            def parse(self, response: Response):
                fetched.append(response.url)

        spider = MySpider(concurrency=1)
        crawler = SyncLiteCrawler(spider)
        crawler.crawl()
        assert len(fetched) == 1


class TestSyncLiteSpiderFetchBranches:
    def test_per_request_proxy_temp_client(self, mock_server):
        """per-request proxy 与全局不同时创建临时 client。"""

        class MySpider(SyncLiteSpider):
            def start_requests(self) -> Generator[Request, None, None]:
                yield Request(url=f"{mock_server}/ok", proxy="127.0.0.1:9999")

            def parse(self, response: Response):
                pass

        spider = MySpider(concurrency=1)
        crawler = SyncLiteCrawler(spider)
        crawler.crawl()
        # 通过不可达代理，请求会失败
        assert crawler.stats["failed"] >= 1

    def test_max_redirects_temp_client(self, mock_server):
        """max_redirects != 20 时创建临时 client。"""
        fetched: list[str] = []

        class MySpider(SyncLiteSpider):
            def start_requests(self) -> Generator[Request, None, None]:
                yield Request(url=f"{mock_server}/ok", max_redirects=5)

            def parse(self, response: Response):
                fetched.append(response.url)

        spider = MySpider(concurrency=1)
        crawler = SyncLiteCrawler(spider)
        crawler.crawl()
        assert len(fetched) == 1

    def test_fetch_without_open_raises(self):
        """未调用 open() 时 fetch 应抛出 RuntimeError。"""

        class MySpider(SyncLiteSpider):
            def start_requests(self) -> Generator[Request, None, None]:
                yield Request(url="http://example.com")

            def parse(self, response: Response):
                pass

        spider = MySpider()
        with pytest.raises(RuntimeError, match="Client not initialized"):
            spider.fetch(Request(url="http://example.com"))

    def test_custom_should_retry(self, mock_server):
        """自定义 should_retry 策略。"""

        class MySpider(SyncLiteSpider):
            def should_retry(self, response: Response) -> bool:
                return response.status == 404  # 只对 404 重试

            def start_requests(self) -> Generator[Request, None, None]:
                yield Request(url=f"{mock_server}/error")  # 500

            def parse(self, response: Response):
                pass

        spider = MySpider(concurrency=1, retry=3)
        crawler = SyncLiteCrawler(spider)
        crawler.crawl()
        # 500 不触发重试（自定义只对 404 重试）
        assert crawler.stats["retried"] == 0

    def test_process_item_exception_logged(self, mock_server):
        """process_item 抛异常时不影响其他 Item。"""

        class MySpider(SyncLiteSpider):
            def start_requests(self) -> Generator[Request, None, None]:
                yield Request(url=f"{mock_server}/ok")

            def parse(self, response: Response):
                yield _TestItem(url=response.url)

            def process_item(self, item: Item):
                raise ValueError("process_item error")

        spider = MySpider(concurrency=1)
        crawler = SyncLiteCrawler(spider)
        crawler.crawl()
        # Item 仍被收集到 crawler.items
        assert len(crawler.items) == 1

    def test_callback_routing(self, mock_server):
        """Request.callback 路由到自定义方法。"""
        custom_results: list[str] = []

        class MySpider(SyncLiteSpider):
            def start_requests(self) -> Generator[Request, None, None]:
                yield Request(url=f"{mock_server}/ok", callback=self.custom_parse)

            def custom_parse(self, response: Response):
                custom_results.append(response.url)

            def parse(self, response: Response):
                pass

        spider = MySpider(concurrency=1)
        crawler = SyncLiteCrawler(spider)
        crawler.crawl()
        assert len(custom_results) == 1

    def test_stats_property(self, mock_server):
        """stats 属性返回副本。"""

        class MySpider(SyncLiteSpider):
            def start_requests(self) -> Generator[Request, None, None]:
                yield Request(url=f"{mock_server}/ok")

            def parse(self, response: Response):
                pass

        spider = MySpider(concurrency=1)
        crawler = SyncLiteCrawler(spider)
        crawler.crawl()
        stats = crawler.stats
        assert stats["requested"] == 1
        assert stats["succeeded"] == 1
        # 修改副本不影响内部状态
        stats["requested"] = 999
        assert crawler.stats["requested"] == 1

    def test_items_property_returns_copy(self, mock_server):
        """items 属性返回副本。"""

        class MySpider(SyncLiteSpider):
            def start_requests(self) -> Generator[Request, None, None]:
                yield Request(url=f"{mock_server}/ok")

            def parse(self, response: Response):
                yield _TestItem(url=response.url)

        spider = MySpider(concurrency=1)
        crawler = SyncLiteCrawler(spider)
        crawler.crawl()
        items = crawler.items
        assert len(items) == 1
        items.clear()
        assert len(crawler.items) == 1

    def test_retry_zero_no_requests(self, mock_server):
        """retry=0 时不发起任何请求。"""

        class MySpider(SyncLiteSpider):
            def start_requests(self) -> Generator[Request, None, None]:
                yield Request(url=f"{mock_server}/ok")

            def parse(self, response: Response):
                pass

        spider = MySpider(concurrency=1, retry=0)
        crawler = SyncLiteCrawler(spider)
        crawler.crawl()
        assert crawler.stats["succeeded"] == 0

    def test_dedup_disabled(self, mock_server):
        """dedup=False 时不去重。"""
        fetched: list[str] = []

        class MySpider(SyncLiteSpider):
            @property
            def dedup(self) -> bool:
                return False

            def start_requests(self) -> Generator[Request, None, None]:
                yield Request(url=f"{mock_server}/ok")
                yield Request(url=f"{mock_server}/ok")

            def parse(self, response: Response):
                fetched.append(response.url)

        spider = MySpider(concurrency=1)
        crawler = SyncLiteCrawler(spider)
        crawler.crawl()
        assert len(fetched) == 2

    def test_dont_filter_meta(self, mock_server):
        """meta dont_filter=True 跳过去重。"""
        fetched: list[str] = []

        class MySpider(SyncLiteSpider):
            def start_requests(self) -> Generator[Request, None, None]:
                yield Request(url=f"{mock_server}/ok")
                yield Request(url=f"{mock_server}/ok", meta={"dont_filter": True})

            def parse(self, response: Response):
                fetched.append(response.url)

        spider = MySpider(concurrency=1)
        crawler = SyncLiteCrawler(spider)
        crawler.crawl()
        assert len(fetched) == 2


class TestSyncLiteCrawlerBranches:
    def test_max_depth_drops_request(self, mock_server):
        """超过 max_depth 的请求被丢弃。"""
        fetched: list[str] = []

        class MySpider(SyncLiteSpider):
            @property
            def max_depth(self) -> int:
                return 1

            def start_requests(self) -> Generator[Request, None, None]:
                yield Request(url=f"{mock_server}/ok")

            def parse(self, response: Response):
                fetched.append(response.url)
                # depth 0 -> 产出 depth 1（允许）-> 产出 depth 2（丢弃）
                yield Request(url=f"{mock_server}/ok?d=1")
                yield Request(url=f"{mock_server}/ok?d=1b")

        spider = MySpider(concurrency=1)
        crawler = SyncLiteCrawler(spider)
        crawler.crawl()
        assert crawler.stats["dropped"] >= 1

    def test_on_close_exception_logged(self, mock_server):
        """on_close 抛异常时不影响关闭流程。"""

        class MySpider(SyncLiteSpider):
            def start_requests(self) -> Generator[Request, None, None]:
                yield Request(url=f"{mock_server}/ok")

            def parse(self, response: Response):
                pass

            def on_close(self):
                raise ValueError("on_close boom")

        spider = MySpider(concurrency=1)
        crawler = SyncLiteCrawler(spider)
        crawler.crawl()  # should not raise

    def test_close_exception_logged(self, mock_server):
        """close 抛异常时不影响关闭流程。"""

        class MySpider(SyncLiteSpider):
            def start_requests(self) -> Generator[Request, None, None]:
                yield Request(url=f"{mock_server}/ok")

            def parse(self, response: Response):
                pass

            def close(self):
                raise ValueError("close boom")

        spider = MySpider(concurrency=1)
        crawler = SyncLiteCrawler(spider)
        crawler.crawl()  # should not raise

    def test_parse_exception_logged(self, mock_server):
        """parse 抛异常时记录日志，不影响其他请求。"""
        fetched: list[str] = []

        class MySpider(SyncLiteSpider):
            def start_requests(self) -> Generator[Request, None, None]:
                yield Request(url=f"{mock_server}/ok")
                yield Request(url=f"{mock_server}/ok?n=2")

            def parse(self, response: Response):
                if "n=2" in response.url:
                    raise ValueError("parse boom")
                fetched.append(response.url)

        spider = MySpider(concurrency=1)
        crawler = SyncLiteCrawler(spider)
        crawler.crawl()
        assert len(fetched) == 1

    def test_fetch_exception_marks_failed(self, mock_server):
        """fetch 抛异常（非返回 status=0）时标记 failed。"""

        class MySpider(SyncLiteSpider):
            def start_requests(self) -> Generator[Request, None, None]:
                yield Request(url=f"{mock_server}/ok")

            def parse(self, response: Response):
                pass

            def fetch(self, request: Request) -> Response:
                raise RuntimeError("fetch boom")

        spider = MySpider(concurrency=1, retry=1)
        crawler = SyncLiteCrawler(spider)
        crawler.crawl()
        assert crawler.stats["failed"] >= 1
