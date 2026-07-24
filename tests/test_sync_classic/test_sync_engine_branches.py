"""SyncEngine 未覆盖分支的单元测试。

直接实例化 SyncEngine + mock 组件，覆盖：
- _get_downloader 无效类
- _crawl_start_requests: StopIteration + not idle / Exception + not idle
- _crawl_task_requests: Exception 路径
- _fetch: download_result 为 Request / response 为 None
- _do_download: 异常 + 中间件处理
- _process_response_middleware: 无中间件 / 返回 None / 返回 Request
- _process_request_middleware: 无中间件
- _handle_success_response: spider middleware 异常
- _handle_error_response: 无 error_callback
- _handle_spider_output: 非法输出类型
- close_spider: 等待任务完成
"""

import threading
from collections.abc import Generator
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from maize import Request, Response, SpiderSettings
from maize.common.items import Item
from maize.common.items.field import Field
from maize.common.model.download_response_model import DownloadResponse
from maize.exceptions.spider_exception import OutputException
from maize.sync.classic.crawler.sync_crawler import SyncCrawler
from maize.sync.classic.engine.sync_engine import SyncEngine
from maize.sync.classic.spider.sync_spider import SyncSpider
from maize.utils.log_util import set_spider_settings


class _TestItem(Item):
    url: str = Field()


class _ConcreteSpider(SyncSpider):
    def start_requests(self) -> Generator[Request, Any, None]:
        yield Request(url="http://example.com")

    def parse(self, response: Response):
        pass


@pytest.fixture(autouse=True)
def _setup():
    set_spider_settings(SpiderSettings())


def _make_engine() -> SyncEngine:
    """创建带 mock 组件的 SyncEngine。"""
    settings = SpiderSettings(project_name="test", concurrency=1)
    crawler = MagicMock(spec=SyncCrawler)
    crawler.settings = settings
    crawler.spider = None
    crawler.idle.return_value = True

    engine = SyncEngine(crawler)
    engine.spider = _ConcreteSpider.__new__(_ConcreteSpider)
    engine.spider._lock = threading.Lock()
    engine.spider.gte_priority = None
    engine.spider.logger = engine.logger
    engine.spider.stats_collector = MagicMock()
    crawler.spider = engine.spider

    engine.scheduler = MagicMock()
    engine.scheduler.idle.return_value = True
    engine.scheduler.next_request.return_value = None

    engine.downloader = MagicMock()
    engine.downloader.idle.return_value = True

    engine.processor = MagicMock()
    engine.processor.idle.return_value = True

    engine.task_manager = MagicMock()
    engine.task_manager.all_done.return_value = True
    engine.task_manager.semaphore = threading.Semaphore(1)

    return engine


class TestGetDownloader:
    def test_invalid_downloader_raises_type_error(self):
        engine = _make_engine()
        engine.settings.downloader = "maize.utils.log_util.get_logger"
        with pytest.raises(TypeError, match="does not fully implement"):
            engine._get_downloader()


class TestCrawlStartRequestsBranches:
    def test_stop_iteration_not_idle_then_idle(self):
        """StopIteration 时 _idle() 先 False 再 True。"""
        engine = _make_engine()
        engine.start_requests_running = True
        engine.running = True

        # 空生成器
        engine.start_requests = iter([])
        engine.spider_middleware_manager = None

        idle_calls = [False, True]
        engine.scheduler.idle.side_effect = lambda: idle_calls.pop(0) if idle_calls else True
        engine.downloader.idle.return_value = True
        engine.processor.idle.return_value = True
        engine.task_manager.all_done.return_value = True
        engine.crawler.idle.return_value = True

        engine._crawl_start_requests()
        assert engine.start_requests_running is False

    def test_exception_not_idle_then_idle(self):
        """start_requests 迭代抛异常，_idle() 先 False 再 True。"""
        engine = _make_engine()
        engine.start_requests_running = True
        engine.running = True

        def bad_gen():
            yield Request(url="http://example.com")
            raise ValueError("boom")

        engine.start_requests = bad_gen()
        engine.spider_middleware_manager = None

        # _get_next_request 始终返回 None，让 next(start_requests) 驱动流程
        engine.scheduler.next_request.return_value = None

        idle_calls = [False, True]

        def mock_idle():
            if idle_calls:
                return idle_calls.pop(0)
            return True

        engine.scheduler.idle.side_effect = lambda: True
        engine.downloader.idle.return_value = True
        engine.processor.idle.return_value = True
        engine.task_manager.all_done.return_value = True
        engine.crawler.idle.return_value = True

        with patch.object(engine, "_idle", side_effect=mock_idle):
            engine._crawl_start_requests()
        assert engine.start_requests_running is False

    def test_no_spider_middleware_manager(self):
        """无 spider_middleware_manager 时直接使用 start_requests。"""
        engine = _make_engine()
        engine.start_requests_running = True
        engine.running = True
        engine.spider_middleware_manager = None

        req = Request(url="http://example.com")
        engine.start_requests = iter([req])
        engine.scheduler.next_request.return_value = None

        engine._crawl_start_requests()
        assert engine.start_requests_running is False
        engine.scheduler.enqueue_request.assert_called_once_with(req)


class TestCrawlTaskRequestsBranches:
    def test_exception_path(self):
        """task_requests 迭代抛异常。"""
        engine = _make_engine()
        engine._single_task_requests_running = True
        engine.task_requests_running = True

        def bad_gen():
            raise ValueError("task boom")
            yield

        engine.task_requests = bad_gen()
        engine.scheduler.next_request.return_value = None

        # _idle() 返回 True 直接退出
        engine.scheduler.idle.return_value = True
        engine.downloader.idle.return_value = True
        engine.processor.idle.return_value = True
        engine.task_manager.all_done.return_value = True
        engine.crawler.idle.return_value = True

        engine._crawl_task_requests()
        assert engine._single_task_requests_running is False

    def test_exception_not_idle_then_idle(self):
        """task_requests 异常 + _idle() 先 False 再 True。"""
        engine = _make_engine()
        engine._single_task_requests_running = True
        engine.task_requests_running = True

        def bad_gen():
            raise ValueError("task boom")
            yield

        engine.task_requests = bad_gen()
        engine.scheduler.next_request.return_value = None

        idle_calls = [False, True]

        def mock_idle():
            if idle_calls:
                return idle_calls.pop(0)
            return True

        with patch.object(engine, "_idle", side_effect=mock_idle):
            engine._crawl_task_requests()
        assert engine._single_task_requests_running is False


class TestFetchBranches:
    def test_download_result_is_request(self):
        """_do_download 返回 Request 时入队。"""
        engine = _make_engine()
        engine.downloader_middleware_manager = None
        engine.spider_middleware_manager = None

        req = Request(url="http://example.com")
        retry_req = Request(url="http://example.com/retry")
        engine.downloader.fetch.return_value = retry_req

        result = engine._fetch(req)
        assert result is None
        engine.scheduler.enqueue_request.assert_called_once_with(retry_req)

    def test_download_result_none(self):
        """_do_download 返回 None。"""
        engine = _make_engine()
        engine.downloader_middleware_manager = None
        engine.spider_middleware_manager = None

        req = Request(url="http://example.com")
        engine.downloader.fetch.return_value = None

        result = engine._fetch(req)
        assert result is None

    def test_download_response_none(self):
        """download_result.response 为 None 时记录失败。"""
        engine = _make_engine()
        engine.downloader_middleware_manager = None
        engine.spider_middleware_manager = None

        req = Request(url="http://example.com")
        engine.downloader.fetch.return_value = DownloadResponse(reason="timeout")

        result = engine._fetch(req)
        assert result is None
        engine.spider.stats_collector.record_download_fail.assert_called_once_with("timeout")

    def test_process_response_middleware_returns_none(self):
        """_process_response_middleware 返回 None。"""
        engine = _make_engine()
        engine.spider_middleware_manager = None

        req = Request(url="http://example.com")
        resp = Response(url="http://example.com", headers={}, status=200, body=b"ok", request=req)
        engine.downloader.fetch.return_value = DownloadResponse(response=resp)

        # 中间件返回 None
        engine.downloader_middleware_manager = MagicMock()
        engine.downloader_middleware_manager.process_response.return_value = None

        result = engine._fetch(req)
        assert result is None


class TestDoDownloadException:
    def test_exception_no_middleware_raises(self):
        """无中间件时异常直接抛出。"""
        engine = _make_engine()
        engine.downloader_middleware_manager = None
        engine.downloader.fetch.side_effect = ConnectionError("fail")

        req = Request(url="http://example.com")
        with pytest.raises(ConnectionError):
            engine._do_download(req)

    def test_exception_middleware_returns_none_raises(self):
        """中间件 process_exception 返回 None 时抛出。"""
        engine = _make_engine()
        engine.downloader_middleware_manager = MagicMock()
        engine.downloader_middleware_manager.process_exception.return_value = None
        engine.downloader.fetch.side_effect = ConnectionError("fail")

        req = Request(url="http://example.com")
        with pytest.raises(ConnectionError):
            engine._do_download(req)

    def test_exception_middleware_returns_request(self):
        """中间件返回 Request 时入队。"""
        engine = _make_engine()
        engine.downloader_middleware_manager = MagicMock()
        retry_req = Request(url="http://example.com/retry")
        engine.downloader_middleware_manager.process_exception.return_value = retry_req
        engine.downloader.fetch.side_effect = ConnectionError("fail")

        req = Request(url="http://example.com")
        result = engine._do_download(req)
        assert result is None
        engine.scheduler.enqueue_request.assert_called_once_with(retry_req)

    def test_exception_middleware_returns_response(self):
        """中间件返回 Response 时包装为 DownloadResponse。"""
        engine = _make_engine()
        engine.downloader_middleware_manager = MagicMock()
        resp = Response(
            url="http://example.com", headers={}, status=200, body=b"ok", request=Request(url="http://example.com")
        )
        engine.downloader_middleware_manager.process_exception.return_value = resp
        engine.downloader.fetch.side_effect = ConnectionError("fail")

        req = Request(url="http://example.com")
        result = engine._do_download(req)
        assert result is not None
        assert result.response is resp


class TestProcessResponseMiddleware:
    def test_no_middleware_manager(self):
        """无中间件管理器时直接返回 response。"""
        engine = _make_engine()
        engine.downloader_middleware_manager = None

        req = Request(url="http://example.com")
        resp = Response(url="http://example.com", headers={}, status=200, body=b"ok", request=req)
        result = engine._process_response_middleware(req, resp)
        assert result is resp

    def test_returns_none(self):
        """中间件返回 None。"""
        engine = _make_engine()
        engine.downloader_middleware_manager = MagicMock()
        engine.downloader_middleware_manager.process_response.return_value = None

        req = Request(url="http://example.com")
        resp = Response(url="http://example.com", headers={}, status=200, body=b"ok", request=req)
        result = engine._process_response_middleware(req, resp)
        assert result is None

    def test_returns_request(self):
        """中间件返回 Request 时入队并返回 None。"""
        engine = _make_engine()
        engine.downloader_middleware_manager = MagicMock()
        retry_req = Request(url="http://example.com/retry")
        engine.downloader_middleware_manager.process_response.return_value = retry_req

        req = Request(url="http://example.com")
        resp = Response(url="http://example.com", headers={}, status=200, body=b"ok", request=req)
        result = engine._process_response_middleware(req, resp)
        assert result is None
        engine.scheduler.enqueue_request.assert_called_once_with(retry_req)


class TestProcessRequestMiddleware:
    def test_no_middleware_manager(self):
        """无中间件管理器时直接返回 request。"""
        engine = _make_engine()
        engine.downloader_middleware_manager = None

        req = Request(url="http://example.com")
        result = engine._process_request_middleware(req)
        assert result is req


class TestHandleSuccessResponseBranches:
    def test_spider_middleware_exception(self):
        """spider middleware process_spider_input 抛异常。"""
        engine = _make_engine()
        engine.spider_middleware_manager = MagicMock()
        engine.spider_middleware_manager.process_spider_input.side_effect = ValueError("mw boom")

        req = Request(url="http://example.com")
        resp = Response(url="http://example.com", headers={}, status=200, body=b"ok", request=req)
        result = engine._handle_success_response(resp, req)
        assert result is None

    def test_spider_middleware_returns_false(self):
        """spider middleware process_spider_input 返回 False。"""
        engine = _make_engine()
        engine.spider_middleware_manager = MagicMock()
        engine.spider_middleware_manager.process_spider_input.return_value = False

        req = Request(url="http://example.com")
        resp = Response(url="http://example.com", headers={}, status=200, body=b"ok", request=req)
        result = engine._handle_success_response(resp, req)
        assert result is None


class TestHandleErrorResponse:
    def test_no_error_callback(self):
        """无 error_callback 时返回 None。"""
        engine = _make_engine()
        req = Request(url="http://example.com")
        result = engine._handle_error_response(req)
        assert result is None


class TestHandleSpiderOutput:
    def test_invalid_output_type_raises(self):
        """输出非法类型时抛 OutputException。"""
        engine = _make_engine()

        def bad_gen():
            yield "not_a_request_or_item"

        with pytest.raises(OutputException):
            engine._handle_spider_output(bad_gen())


class TestCloseSpider:
    def test_close_spider_waits_for_tasks(self):
        """close_spider 等待 task_manager.all_done()。"""
        engine = _make_engine()
        engine.downloader_middleware_manager = MagicMock()
        engine.spider_middleware_manager = MagicMock()

        # 第一次 all_done 返回 False，第二次返回 True
        engine.task_manager.all_done.side_effect = [False, True]

        engine.close_spider()
        engine.downloader_middleware_manager.close.assert_called_once()
        engine.spider_middleware_manager.close.assert_called_once()
        engine.downloader.close.assert_called_once()
        engine.processor.close.assert_called_once()
        engine.task_manager.close.assert_called_once()
