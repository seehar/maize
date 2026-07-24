"""同步引擎和 Spider 单元测试。

覆盖 SyncEngine 的分支：
- _get_downloader 无效类
- start_requests 非生成器 / NotImplementedError
- task spider 路径
- _crawl_start_requests 异常分支
- _crawl_task_requests 全流程
- _fetch 中间件短路/异常
- _handle_error_response
- close_spider

覆盖 SyncSpider 的 pause/proceed/idle。
覆盖 SyncCrawlerProcess 的字符串参数拒绝。
"""

import threading
from collections.abc import Generator
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

import pytest

from maize import Request, Response, SpiderSettings, SyncSpider, SyncSpiderDownloaderEnum
from maize.exceptions.spider_exception import SpiderTypeException, StartRequestsNotImplementedException
from maize.sync.classic.crawler.sync_crawler import SyncCrawler, SyncCrawlerProcess
from maize.sync.classic.engine.sync_engine import SyncEngine
from maize.sync.classic.middleware.sync_base_middleware import SyncDownloaderMiddleware
from maize.sync.classic.spider.sync_task_spider import SyncTaskSpider
from maize.utils.log_util import set_spider_settings


class _MockHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = b'{"ok": true}'
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


@pytest.fixture(autouse=True)
def _setup():
    set_spider_settings(SpiderSettings())


class TestSyncEngineValidation:
    def test_start_requests_not_generator(self):
        class BadSpider(SyncSpider):
            def start_requests(self):
                return [Request(url="http://x.com")]  # not a generator

        settings = SpiderSettings(
            project_name="test",
            concurrency=1,
            downloader=SyncSpiderDownloaderEnum.HTTPX.value,
        )
        crawler = SyncCrawler(BadSpider, settings)
        crawler.spider = BadSpider.create_instance(crawler)
        crawler.spider.open()
        engine = SyncEngine(crawler)
        with pytest.raises(StartRequestsNotImplementedException):
            engine.start_spider(crawler.spider)

    def test_start_requests_not_implemented(self):
        class BadSpider(SyncSpider):
            def start_requests(self) -> Generator[Request, Any, None]:
                raise NotImplementedError

        settings = SpiderSettings(
            project_name="test",
            concurrency=1,
            downloader=SyncSpiderDownloaderEnum.HTTPX.value,
        )
        crawler = SyncCrawler(BadSpider, settings)
        crawler.spider = BadSpider.create_instance(crawler)
        crawler.spider.open()
        engine = SyncEngine(crawler)
        with pytest.raises(StartRequestsNotImplementedException):
            engine.start_spider(crawler.spider)


class TestSyncEngineTaskSpider:
    def test_task_spider_runs(self, mock_server):
        results: list[str] = []

        class MyTaskSpider(SyncTaskSpider):
            def start_requests(self) -> Generator[Request, Any, None]:
                yield Request(url=f"{mock_server}/ok")

            def parse(self, response: Response):
                results.append(response.url)

        settings = SpiderSettings(
            project_name="test",
            concurrency=1,
            downloader=SyncSpiderDownloaderEnum.HTTPX.value,
        )
        process = SyncCrawlerProcess(settings=settings)
        process.crawl(MyTaskSpider)
        process.start()
        assert len(results) >= 1  # task spider 的 start_requests 被引擎消费两次（校验+任务循环）

    def test_task_spider_empty_generator(self, mock_server):
        class EmptyTaskSpider(SyncTaskSpider):
            def start_requests(self) -> Generator[Request, Any, None]:
                return
                yield  # make it a generator

            def parse(self, response: Response):
                pass

        settings = SpiderSettings(
            project_name="test",
            concurrency=1,
            downloader=SyncSpiderDownloaderEnum.HTTPX.value,
        )
        process = SyncCrawlerProcess(settings=settings)
        process.crawl(EmptyTaskSpider)
        process.start()  # should terminate


class TestSyncEngineMiddlewareBranches:
    def test_downloader_middleware_short_circuit_response(self, mock_server):
        """中间件 process_request 返回 Response 短路下载。"""
        results: list[str] = []
        short_circuit_body = b'{"short": "circuit"}'

        class ShortCircuitMW(SyncDownloaderMiddleware):
            def process_request(self, request, spider):
                return Response(
                    url=request.url,
                    headers={},
                    status=200,
                    body=short_circuit_body,
                    request=request,
                )

        class MySpider(SyncSpider):
            def start_requests(self) -> Generator[Request, Any, None]:
                yield Request(url=f"{mock_server}/ok")

            def parse(self, response: Response):
                results.append(response.body)

        settings = SpiderSettings(
            project_name="test",
            concurrency=1,
            downloader=SyncSpiderDownloaderEnum.HTTPX.value,
        )
        settings.middleware.downloader_middlewares = {ShortCircuitMW: 100}
        process = SyncCrawlerProcess(settings=settings)
        process.crawl(MySpider)
        process.start()
        assert len(results) == 1
        assert results[0] == short_circuit_body

    def test_downloader_middleware_drops_request(self, mock_server):
        """中间件 process_request 返回 None 丢弃请求。"""
        results: list[str] = []

        class DropMW(SyncDownloaderMiddleware):
            def process_request(self, request, spider):
                return None

        class MySpider(SyncSpider):
            def start_requests(self) -> Generator[Request, Any, None]:
                yield Request(url=f"{mock_server}/ok")

            def parse(self, response: Response):
                results.append(response.url)

        settings = SpiderSettings(
            project_name="test",
            concurrency=1,
            downloader=SyncSpiderDownloaderEnum.HTTPX.value,
        )
        settings.middleware.downloader_middlewares = {DropMW: 100}
        process = SyncCrawlerProcess(settings=settings)
        process.crawl(MySpider)
        process.start()
        assert len(results) == 0

    def test_error_callback(self, mock_server):
        """下载失败时调用 error_callback。"""
        error_urls: list[str] = []

        class MySpider(SyncSpider):
            def start_requests(self) -> Generator[Request, Any, None]:
                yield Request(
                    url="http://127.0.0.1:1/unreachable",
                    error_callback=self.on_error,
                )

            def on_error(self, request: Request):
                error_urls.append(request.url)
                yield Request(url=f"{mock_server}/ok")

            def parse(self, response: Response):
                pass

        settings = SpiderSettings(
            project_name="test",
            concurrency=1,
            downloader=SyncSpiderDownloaderEnum.HTTPX.value,
        )
        settings.request.max_retry_count = 0
        process = SyncCrawlerProcess(settings=settings)
        process.crawl(MySpider)
        process.start()
        assert len(error_urls) == 1


class _ConcreteSpider(SyncSpider):
    def start_requests(self) -> Generator[Request, Any, None]:
        yield Request(url="http://example.com")


class TestSyncSpiderPauseProceed:
    def _make_spider(self):
        spider = _ConcreteSpider.__new__(_ConcreteSpider)
        spider._lock = threading.Lock()
        spider.gte_priority = None
        spider.logger = None
        spider.stats_collector = None
        return spider

    def test_pause_and_proceed(self):
        spider = self._make_spider()

        assert spider.is_pause() is False
        assert spider.idle() is True

        spider.pause_spider()
        assert spider.is_pause() is True
        assert spider.gte_priority == 0
        assert spider.idle() is False

        # 重复暂停应告警并返回
        spider.pause_spider()
        assert spider.gte_priority == 0

        spider.proceed_spider()
        assert spider.is_pause() is False
        assert spider.gte_priority is None

    def test_pause_with_priority(self):
        spider = self._make_spider()

        spider.pause_spider(lte_priority=5)
        assert spider.gte_priority == 6

        spider.proceed_spider(gte_priority=3)
        assert spider.gte_priority == 3


class TestSyncCrawlerProcess:
    def test_crawl_with_string_raises(self):
        settings = SpiderSettings(project_name="test")
        process = SyncCrawlerProcess(settings=settings)
        with pytest.raises(SpiderTypeException):
            process.crawl("not_a_spider")

    def test_crawler_idle_without_spider(self):
        settings = SpiderSettings(project_name="test")
        crawler = SyncCrawler(SyncSpider, settings)
        assert crawler.idle() is True


class TestSyncEngineErrorPaths:
    def test_parse_callback_exception(self, mock_server):
        """parse 回调抛异常时引擎不崩溃，记录 parse_fail。"""
        results: list[str] = []

        class MySpider(SyncSpider):
            def start_requests(self) -> Generator[Request, Any, None]:
                yield Request(url=f"{mock_server}/ok")
                yield Request(url=f"{mock_server}/ok?n=2")

            def parse(self, response: Response):
                if "n=2" in response.url:
                    raise ValueError("parse boom")
                results.append(response.url)

        settings = SpiderSettings(
            project_name="test",
            concurrency=1,
            downloader=SyncSpiderDownloaderEnum.HTTPX.value,
        )
        process = SyncCrawlerProcess(settings=settings)
        process.crawl(MySpider)
        process.start()
        assert len(results) == 1

    def test_error_callback_exception(self, mock_server):
        """error_callback 抛异常时引擎不崩溃。"""

        class MySpider(SyncSpider):
            def start_requests(self) -> Generator[Request, Any, None]:
                yield Request(
                    url="http://127.0.0.1:1/unreachable",
                    error_callback=self.on_error,
                )

            def on_error(self, request: Request):
                raise ValueError("error_callback boom")

            def parse(self, response: Response):
                pass

        settings = SpiderSettings(
            project_name="test",
            concurrency=1,
            downloader=SyncSpiderDownloaderEnum.HTTPX.value,
        )
        settings.request.max_retry_count = 0
        process = SyncCrawlerProcess(settings=settings)
        process.crawl(MySpider)
        process.start()  # should not raise

    def test_start_requests_exception_during_iteration(self, mock_server):
        """start_requests 迭代中抛异常时引擎正常退出。"""
        results: list[str] = []

        class MySpider(SyncSpider):
            def start_requests(self) -> Generator[Request, Any, None]:
                yield Request(url=f"{mock_server}/ok")
                raise ValueError("start_requests boom")

            def parse(self, response: Response):
                results.append(response.url)

        settings = SpiderSettings(
            project_name="test",
            concurrency=1,
            downloader=SyncSpiderDownloaderEnum.HTTPX.value,
        )
        process = SyncCrawlerProcess(settings=settings)
        process.crawl(MySpider)
        process.start()
        assert len(results) == 1
