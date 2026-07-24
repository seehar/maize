"""SyncLiteCrawler 未覆盖分支的单元测试。

覆盖：
- 信号处理器注册失败（非主线程）
- feed_start_requests 中 stop_event 中断
- worker 中 stop_event 中断
- worker 中 _process 异常
- _fetch_with_retry 中 stop_event 中断重试
"""

import threading
from unittest.mock import MagicMock, patch

from maize import Request, Response
from maize.sync.lite.crawler.sync_lite_crawler import SyncLiteCrawler


class _FakeSpider:
    """模拟 SyncLiteSpider 的最小实现。"""

    def __init__(self):
        self.concurrency = 1
        self.retry = 3
        self.max_depth = 0
        self.dedup = False
        self.per_domain_concurrency = 0
        self.logger = MagicMock()
        self._opened = False
        self._closed = False
        self._on_start_called = False
        self._on_close_called = False

    def open(self):
        self._opened = True

    def close(self):
        self._closed = True

    def on_start(self):
        self._on_start_called = True

    def on_close(self):
        self._on_close_called = True

    def start_requests(self):
        yield Request(url="http://example.com")

    def parse(self, response):
        pass

    def fetch(self, request):
        return Response(url=request.url, headers={}, status=200, body=b"ok", request=request)

    def should_retry(self, response):
        return response.status == 0 or response.status >= 500 or response.status == 429

    def process_item(self, item):
        pass


class TestSignalHandlerRegistration:
    def test_signal_registration_failure_in_non_main_thread(self):
        """非主线程注册信号处理器失败时静默跳过。"""
        spider = _FakeSpider()
        crawler = SyncLiteCrawler(spider=spider, concurrency=1)

        # 在非主线程中运行 crawl，signal.signal 会抛 ValueError
        result = []

        def run_in_thread():
            try:
                crawler.crawl()
                result.append("ok")
            except Exception as e:
                result.append(f"error: {e}")

        t = threading.Thread(target=run_in_thread)
        t.start()
        t.join(timeout=10)
        assert result == ["ok"]
        assert spider._on_close_called


class TestFeedStopEvent:
    def test_feed_breaks_on_stop_event(self):
        """feed_start_requests 中 stop_event 设置后中断。"""
        spider = _FakeSpider()

        def slow_start_requests():
            yield Request(url="http://example.com/1")
            # 模拟 stop_event 在 yield 之间被设置
            yield Request(url="http://example.com/2")

        spider.start_requests = slow_start_requests
        crawler = SyncLiteCrawler(spider=spider, concurrency=1)

        # 在 crawl 开始后设置 stop_event
        original_on_start = spider.on_start

        def on_start_with_stop():
            original_on_start()
            crawler._stop_event.set()

        spider.on_start = on_start_with_stop
        crawler.crawl()
        # 应该正常退出，不处理任何请求
        assert spider._on_close_called


class TestWorkerStopEvent:
    def test_worker_breaks_on_stop_event(self):
        """worker 中 stop_event 设置后退出。"""
        spider = _FakeSpider()
        crawler = SyncLiteCrawler(spider=spider, concurrency=1)

        # 在 feed 完成后设置 stop_event
        original_on_start = spider.on_start

        def on_start_with_stop():
            original_on_start()
            # 延迟设置 stop_event
            threading.Timer(0.1, crawler._stop_event.set).start()

        spider.on_start = on_start_with_stop
        crawler.crawl()
        assert spider._on_close_called


class TestWorkerProcessException:
    def test_worker_catches_process_exception(self):
        """worker 中 _process 抛异常时不崩溃。"""
        spider = _FakeSpider()
        crawler = SyncLiteCrawler(spider=spider, concurrency=1)

        with patch.object(crawler, "_process", side_effect=ValueError("process boom")):
            crawler.crawl()
        assert spider._on_close_called


class TestFetchWithRetryStopEvent:
    def test_retry_aborted_by_stop_event(self):
        """重试等待期间收到停止信号，中止后续重试。"""
        spider = _FakeSpider()
        spider.retry = 5
        call_count = [0]

        def failing_fetch(request):
            call_count[0] += 1
            return Response(url=request.url, headers={}, status=500, body=b"err", request=request)

        spider.fetch = failing_fetch
        crawler = SyncLiteCrawler(spider=spider, concurrency=1)

        # 在第一次重试等待时设置 stop_event

        def mock_wait(timeout=None):
            crawler._stop_event.set()
            return True

        with patch.object(crawler._stop_event, "wait", side_effect=mock_wait):
            req = Request(url="http://example.com")
            result = crawler._fetch_with_retry(req)

        assert result.status == 500
        assert call_count[0] == 1  # 第一次 fetch 后重试等待即被 stop_event 中止


class TestQueueEmptyBreak:
    def test_worker_breaks_on_empty_queue_feed_done(self):
        """队列为空且 feed 完成时 worker 退出。"""
        spider = _FakeSpider()
        # 不产出任何请求
        spider.start_requests = lambda: iter([])
        crawler = SyncLiteCrawler(spider=spider, concurrency=1)
        crawler.crawl()
        assert spider._on_close_called
