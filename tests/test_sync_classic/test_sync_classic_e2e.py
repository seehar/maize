"""同步 Classic 爬虫端到端测试。

使用本地 mock HTTP server 验证 SyncClassic 全链路：
- start_requests → 中间件 → 下载 → parse → Item → 管道
- 自定义中间件调用链
- 自定义管道数据落盘
- SyncCrawlerProcess 运行入口
"""

import threading
import typing
from collections.abc import Generator
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from maize import Request, Response, SpiderSettings, SyncSpider, SyncSpiderDownloaderEnum
from maize.common.items import Item
from maize.common.items.field import Field
from maize.sync.classic.crawler.sync_crawler import SyncCrawlerProcess
from maize.sync.classic.middleware.sync_base_middleware import (
    SyncDownloaderMiddleware,
    SyncSpiderMiddleware,
)
from maize.sync.classic.pipeline.sync_base_pipeline import SyncBasePipeline
from maize.utils.log_util import set_spider_settings


class _MockHandler(BaseHTTPRequestHandler):
    """Mock HTTP handler。"""

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
            body = b'<html><a href="/ok">link</a></html>'
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


@pytest.fixture(autouse=True)
def _setup_settings():
    """每个测试前设置 SpiderSettings 上下文，避免 ContextVar 泄漏。"""
    set_spider_settings(SpiderSettings())


class MyItem(Item):
    """测试用 Item。"""

    url: str = Field()
    status: int = Field()


class TestSyncClassicE2E:
    """SyncClassic 端到端测试。"""

    def test_simple_fetch(self, mock_server):
        """测试 SyncCrawlerProcess 端到端抓取。"""
        results: list[str] = []

        class MySpider(SyncSpider):
            def start_requests(self) -> Generator[Request, typing.Any, None]:
                yield Request(url=f"{mock_server}/ok")

            def parse(self, response: Response):
                results.append(f"{response.status}:{response.url}")

        settings = SpiderSettings(
            project_name="test",
            concurrency=1,
            downloader=SyncSpiderDownloaderEnum.HTTPX.value,
        )
        process = SyncCrawlerProcess(settings=settings)
        process.crawl(MySpider)
        process.start()

        assert len(results) == 1
        assert "200:" in results[0]

    def test_item_pipeline(self, mock_server):
        """测试 Item 收集 + 自定义管道。"""
        collected_items: list[MyItem] = []

        class MyPipeline(SyncBasePipeline):
            def open(self):
                pass

            def close(self):
                pass

            def process_item(self, items: list[Item]) -> bool:
                collected_items.extend(items)
                return True

            def process_error_item(self, items: list[Item]):
                pass

        class MySpider(SyncSpider):
            def start_requests(self) -> Generator[Request, typing.Any, None]:
                yield Request(url=f"{mock_server}/ok")

            def parse(self, response: Response):
                yield MyItem(url=response.url, status=response.status)

        settings = SpiderSettings(
            project_name="test",
            concurrency=1,
            downloader=SyncSpiderDownloaderEnum.HTTPX.value,
        )
        settings.pipeline.pipelines = [MyPipeline]

        process = SyncCrawlerProcess(settings=settings)
        process.crawl(MySpider)
        process.start()

        assert len(collected_items) == 1
        assert collected_items[0].status == 200

    def test_downloader_middleware(self, mock_server):
        """测试下载器中间件 process_request / process_response 调用。"""
        mw_calls: list[str] = []

        class MyDownloaderMiddleware(SyncDownloaderMiddleware):
            def open(self):
                pass

            def close(self):
                pass

            def process_request(self, request: Request, spider: SyncSpider):
                mw_calls.append(f"process_request:{request.url}")
                return request

            def process_response(self, request: Request, response: Response, spider: SyncSpider):
                mw_calls.append(f"process_response:{response.status}")
                return response

        class MySpider(SyncSpider):
            def start_requests(self) -> Generator[Request, typing.Any, None]:
                yield Request(url=f"{mock_server}/ok")

            def parse(self, response: Response):
                pass

        settings = SpiderSettings(
            project_name="test",
            concurrency=1,
            downloader=SyncSpiderDownloaderEnum.HTTPX.value,
        )
        settings.middleware.downloader_middlewares = {MyDownloaderMiddleware: 100}

        process = SyncCrawlerProcess(settings=settings)
        process.crawl(MySpider)
        process.start()

        assert any("process_request" in c for c in mw_calls)
        assert any("process_response" in c for c in mw_calls)

    def test_spider_middleware(self, mock_server):
        """测试爬虫中间件 process_spider_output 调用。"""
        mw_outputs: list[str] = []

        class MySpiderMiddleware(SyncSpiderMiddleware):
            def open(self):
                pass

            def close(self):
                pass

            def process_spider_output(self, response: Response, result: Generator, spider: SyncSpider):
                for item in result:
                    if isinstance(item, Item):
                        mw_outputs.append(f"item:{item.url}")
                    yield item

        class MySpider(SyncSpider):
            def start_requests(self) -> Generator[Request, typing.Any, None]:
                yield Request(url=f"{mock_server}/ok")

            def parse(self, response: Response):
                yield MyItem(url=response.url, status=response.status)

        settings = SpiderSettings(
            project_name="test",
            concurrency=1,
            downloader=SyncSpiderDownloaderEnum.HTTPX.value,
        )
        settings.middleware.spider_middlewares = {MySpiderMiddleware: 100}

        process = SyncCrawlerProcess(settings=settings)
        process.crawl(MySpider)
        process.start()

        assert any("item:" in c for c in mw_outputs)

    def test_concurrent_fetch(self, mock_server):
        """测试多 URL 并发抓取。"""
        fetched_urls: list[str] = []

        class MySpider(SyncSpider):
            def start_requests(self) -> Generator[Request, typing.Any, None]:
                for _ in range(5):
                    yield Request(url=f"{mock_server}/ok")

            def parse(self, response: Response):
                fetched_urls.append(response.url)

        settings = SpiderSettings(
            project_name="test",
            concurrency=3,
            downloader=SyncSpiderDownloaderEnum.HTTPX.value,
        )

        process = SyncCrawlerProcess(settings=settings)
        process.crawl(MySpider)
        process.start()

        assert len(fetched_urls) == 5
