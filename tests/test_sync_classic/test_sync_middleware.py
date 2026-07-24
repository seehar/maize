"""同步中间件管理器单元测试。

覆盖 SyncMiddlewareManager 基类、三个子管理器的所有分支：
- 加载成功/失败、from_crawler 路径
- process_request/response/exception 各返回值分支
- process_spider_input/output/exception/start_requests
- process_item_before/after
- 异常处理路径
"""

import pytest

from maize import SpiderSettings
from maize.common.http import Request, Response
from maize.common.items import Item
from maize.common.items.field import Field
from maize.sync.classic.middleware.sync_base_middleware import (
    SyncDownloaderMiddleware,
    SyncPipelineMiddleware,
    SyncSpiderMiddleware,
)
from maize.sync.classic.middleware.sync_middleware_manager import (
    SyncDownloaderMiddlewareManager,
    SyncPipelineMiddlewareManager,
    SyncSpiderMiddlewareManager,
)
from maize.utils.log_util import set_spider_settings


class _TestItem(Item):
    url: str = Field()


class _FakeSpider:
    pass


class _FakeCrawler:
    def __init__(self):
        self.settings = SpiderSettings()
        self.spider = _FakeSpider()


@pytest.fixture(autouse=True)
def _setup():
    set_spider_settings(SpiderSettings())


def _make_response(request: Request | None = None) -> Response:
    req = request or Request(url="http://example.com")
    return Response(url="http://example.com", headers={}, status=200, body=b"ok", request=req)


# --- SyncDownloaderMiddlewareManager ---


class TestDownloaderMiddlewareManager:
    def _make_manager(self, middlewares: dict) -> SyncDownloaderMiddlewareManager:
        crawler = _FakeCrawler()
        mgr = SyncDownloaderMiddlewareManager(crawler, middlewares)
        mgr.open()
        return mgr

    def test_process_request_passthrough(self):
        class MW(SyncDownloaderMiddleware):
            def process_request(self, request, spider):
                return request

        mgr = self._make_manager({MW: 100})
        req = Request(url="http://example.com")
        result = mgr.process_request(req, _FakeSpider())
        assert result is req

    def test_process_request_returns_response_short_circuit(self):
        short_circuit_resp = _make_response()

        class MW(SyncDownloaderMiddleware):
            def process_request(self, request, spider):
                return short_circuit_resp

        mgr = self._make_manager({MW: 100})
        req = Request(url="http://example.com")
        result = mgr.process_request(req, _FakeSpider())
        assert isinstance(result, Response)

    def test_process_request_returns_none_drops(self):
        class MW(SyncDownloaderMiddleware):
            def process_request(self, request, spider):
                return None

        mgr = self._make_manager({MW: 100})
        req = Request(url="http://example.com")
        result = mgr.process_request(req, _FakeSpider())
        assert result is None

    def test_process_request_exception_continues(self):
        class MW(SyncDownloaderMiddleware):
            def process_request(self, request, spider):
                raise ValueError("boom")

        mgr = self._make_manager({MW: 100})
        req = Request(url="http://example.com")
        result = mgr.process_request(req, _FakeSpider())
        assert result is req

    def test_process_response_passthrough(self):
        class MW(SyncDownloaderMiddleware):
            def process_response(self, request, response, spider):
                return response

        mgr = self._make_manager({MW: 100})
        req = Request(url="http://example.com")
        resp = _make_response(req)
        result = mgr.process_response(req, resp, _FakeSpider())
        assert result is resp

    def test_process_response_returns_request_retry(self):
        retry_req = Request(url="http://retry.com")

        class MW(SyncDownloaderMiddleware):
            def process_response(self, request, response, spider):
                return retry_req

        mgr = self._make_manager({MW: 100})
        req = Request(url="http://example.com")
        resp = _make_response(req)
        result = mgr.process_response(req, resp, _FakeSpider())
        assert isinstance(result, Request)

    def test_process_response_returns_none_drops(self):
        class MW(SyncDownloaderMiddleware):
            def process_response(self, request, response, spider):
                return None

        mgr = self._make_manager({MW: 100})
        req = Request(url="http://example.com")
        resp = _make_response(req)
        result = mgr.process_response(req, resp, _FakeSpider())
        assert result is None

    def test_process_response_exception_continues(self):
        class MW(SyncDownloaderMiddleware):
            def process_response(self, request, response, spider):
                raise ValueError("boom")

        mgr = self._make_manager({MW: 100})
        req = Request(url="http://example.com")
        resp = _make_response(req)
        result = mgr.process_response(req, resp, _FakeSpider())
        assert result is resp

    def test_process_exception_handled(self):
        retry_req = Request(url="http://retry.com")

        class MW(SyncDownloaderMiddleware):
            def process_exception(self, request, exception, spider):
                return retry_req

        mgr = self._make_manager({MW: 100})
        req = Request(url="http://example.com")
        result = mgr.process_exception(req, ValueError("err"), _FakeSpider())
        assert isinstance(result, Request)

    def test_process_exception_not_handled(self):
        class MW(SyncDownloaderMiddleware):
            def process_exception(self, request, exception, spider):
                return None

        mgr = self._make_manager({MW: 100})
        req = Request(url="http://example.com")
        result = mgr.process_exception(req, ValueError("err"), _FakeSpider())
        assert result is None

    def test_process_exception_inner_exception_continues(self):
        class MW(SyncDownloaderMiddleware):
            def process_exception(self, request, exception, spider):
                raise RuntimeError("inner")

        mgr = self._make_manager({MW: 100})
        req = Request(url="http://example.com")
        result = mgr.process_exception(req, ValueError("err"), _FakeSpider())
        assert result is None

    def test_load_failure_returns_none(self):
        mgr = self._make_manager({"nonexistent.module.Middleware": 100})
        assert len(mgr.middlewares) == 0

    def test_open_exception_logged(self):
        class MW(SyncDownloaderMiddleware):
            def open(self):
                raise ValueError("open failed")

        mgr = self._make_manager({MW: 100})
        assert len(mgr.middlewares) == 1

    def test_close_exception_logged(self):
        class MW(SyncDownloaderMiddleware):
            def close(self):
                raise ValueError("close failed")

        mgr = self._make_manager({MW: 100})
        mgr.close()  # should not raise

    def test_non_downloader_middleware_skipped(self):
        """非 SyncDownloaderMiddleware 类型的中间件在 process_* 中被跳过。"""

        class NotDownloader(SyncSpiderMiddleware):
            pass

        mgr = self._make_manager({NotDownloader: 100})
        req = Request(url="http://example.com")
        result = mgr.process_request(req, _FakeSpider())
        assert result is req


# --- SyncSpiderMiddlewareManager ---


class TestSpiderMiddlewareManager:
    def _make_manager(self, middlewares: dict) -> SyncSpiderMiddlewareManager:
        crawler = _FakeCrawler()
        mgr = SyncSpiderMiddlewareManager(crawler, middlewares)
        mgr.open()
        return mgr

    def test_process_spider_input_continue(self):
        class MW(SyncSpiderMiddleware):
            def process_spider_input(self, response, spider):
                return True

        mgr = self._make_manager({MW: 100})
        resp = _make_response()
        assert mgr.process_spider_input(resp, _FakeSpider()) is True

    def test_process_spider_input_stop(self):
        class MW(SyncSpiderMiddleware):
            def process_spider_input(self, response, spider):
                return False

        mgr = self._make_manager({MW: 100})
        resp = _make_response()
        assert mgr.process_spider_input(resp, _FakeSpider()) is False

    def test_process_spider_input_exception_handled(self):
        class MW(SyncSpiderMiddleware):
            def process_spider_input(self, response, spider):
                raise ValueError("boom")

            def process_spider_exception(self, response, exception, spider):
                return iter([])

        mgr = self._make_manager({MW: 100})
        resp = _make_response()
        assert mgr.process_spider_input(resp, _FakeSpider()) is False

    def test_process_spider_input_exception_unhandled_raises(self):
        class MW(SyncSpiderMiddleware):
            def process_spider_input(self, response, spider):
                raise ValueError("boom")

        mgr = self._make_manager({MW: 100})
        resp = _make_response()
        with pytest.raises(ValueError, match="boom"):
            mgr.process_spider_input(resp, _FakeSpider())

    def test_process_spider_output(self):
        class MW(SyncSpiderMiddleware):
            def process_spider_output(self, response, result, spider):
                yield from result

        mgr = self._make_manager({MW: 100})
        resp = _make_response()

        def gen():
            yield _TestItem(url="http://a.com")

        output = list(mgr.process_spider_output(resp, gen(), _FakeSpider()))
        assert len(output) == 1

    def test_process_spider_output_exception_continues(self):
        class MW(SyncSpiderMiddleware):
            def process_spider_output(self, response, result, spider):
                raise ValueError("boom")

        mgr = self._make_manager({MW: 100})
        resp = _make_response()

        def gen():
            yield _TestItem(url="http://a.com")

        output = list(mgr.process_spider_output(resp, gen(), _FakeSpider()))
        assert len(output) == 1

    def test_process_spider_exception_handled(self):
        class MW(SyncSpiderMiddleware):
            def process_spider_exception(self, response, exception, spider):
                return iter([])

        mgr = self._make_manager({MW: 100})
        resp = _make_response()
        result = mgr.process_spider_exception(resp, ValueError("err"), _FakeSpider())
        assert result is not None

    def test_process_spider_exception_not_handled(self):
        class MW(SyncSpiderMiddleware):
            def process_spider_exception(self, response, exception, spider):
                return None

        mgr = self._make_manager({MW: 100})
        resp = _make_response()
        result = mgr.process_spider_exception(resp, ValueError("err"), _FakeSpider())
        assert result is None

    def test_process_spider_exception_inner_exception(self):
        class MW(SyncSpiderMiddleware):
            def process_spider_exception(self, response, exception, spider):
                raise RuntimeError("inner")

        mgr = self._make_manager({MW: 100})
        resp = _make_response()
        result = mgr.process_spider_exception(resp, ValueError("err"), _FakeSpider())
        assert result is None

    def test_process_start_requests(self):
        class MW(SyncSpiderMiddleware):
            def process_start_requests(self, start_requests, spider):
                yield from start_requests

        mgr = self._make_manager({MW: 100})

        def gen():
            yield Request(url="http://a.com")

        output = list(mgr.process_start_requests(gen(), _FakeSpider()))
        assert len(output) == 1

    def test_process_start_requests_exception_continues(self):
        class MW(SyncSpiderMiddleware):
            def process_start_requests(self, start_requests, spider):
                raise ValueError("boom")

        mgr = self._make_manager({MW: 100})

        def gen():
            yield Request(url="http://a.com")

        output = list(mgr.process_start_requests(gen(), _FakeSpider()))
        assert len(output) == 1


# --- SyncPipelineMiddlewareManager ---


class TestPipelineMiddlewareManager:
    def _make_manager(self, middlewares: dict) -> SyncPipelineMiddlewareManager:
        crawler = _FakeCrawler()
        mgr = SyncPipelineMiddlewareManager(crawler, middlewares)
        mgr.open()
        return mgr

    def test_process_item_before_passthrough(self):
        class MW(SyncPipelineMiddleware):
            def process_item_before(self, item, spider):
                return item

        mgr = self._make_manager({MW: 100})
        item = _TestItem(url="http://a.com")
        result = mgr.process_item_before(item, _FakeSpider())
        assert result is item

    def test_process_item_before_drops(self):
        class MW(SyncPipelineMiddleware):
            def process_item_before(self, item, spider):
                return None

        mgr = self._make_manager({MW: 100})
        item = _TestItem(url="http://a.com")
        result = mgr.process_item_before(item, _FakeSpider())
        assert result is None

    def test_process_item_before_exception_continues(self):
        class MW(SyncPipelineMiddleware):
            def process_item_before(self, item, spider):
                raise ValueError("boom")

        mgr = self._make_manager({MW: 100})
        item = _TestItem(url="http://a.com")
        result = mgr.process_item_before(item, _FakeSpider())
        assert result is item

    def test_process_item_after_passthrough(self):
        class MW(SyncPipelineMiddleware):
            def process_item_after(self, item, spider):
                return item

        mgr = self._make_manager({MW: 100})
        item = _TestItem(url="http://a.com")
        result = mgr.process_item_after(item, _FakeSpider())
        assert result is item

    def test_process_item_after_drops(self):
        class MW(SyncPipelineMiddleware):
            def process_item_after(self, item, spider):
                return None

        mgr = self._make_manager({MW: 100})
        item = _TestItem(url="http://a.com")
        result = mgr.process_item_after(item, _FakeSpider())
        assert result is None

    def test_process_item_after_exception_continues(self):
        class MW(SyncPipelineMiddleware):
            def process_item_after(self, item, spider):
                raise ValueError("boom")

        mgr = self._make_manager({MW: 100})
        item = _TestItem(url="http://a.com")
        result = mgr.process_item_after(item, _FakeSpider())
        assert result is item
