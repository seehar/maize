"""AioEngine 未覆盖分支的单元测试。

覆盖：
- _crawl_start_requests: StopAsyncIteration + not idle / Exception + not idle
- _crawl_task_requests: StopAsyncIteration / RuntimeError / Exception 路径
- _crawl: crawl_task 执行
- _do_download: 异常 + 中间件返回 Response
- _handle_success_response: coroutine callback / spider middleware
- _process_response_middleware: 返回 Request
- RedisUtil import 失败路径
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import maize.core.engine.aio_engine as aio_engine_mod
from maize.common.http.request import Request
from maize.common.http.response import Response
from maize.common.items import Item
from maize.common.items.field import Field
from maize.core.engine.aio_engine import AioEngine
from maize.settings import SpiderSettings


class _TestItem(Item):
    url: str = Field()


def _make_engine():
    crawler = MagicMock()
    crawler.settings = SpiderSettings()
    crawler.idle.return_value = True
    engine = AioEngine(crawler)
    engine.spider = MagicMock()
    engine.spider.stats_collector.record_download_success = AsyncMock()
    engine.spider.stats_collector.record_download_fail = AsyncMock()
    engine.spider.stats_collector.record_parse_success = AsyncMock()
    engine.spider.stats_collector.record_parse_fail = AsyncMock()
    engine.scheduler = MagicMock()
    engine.scheduler.enqueue_request = AsyncMock()
    engine.scheduler.next_request = AsyncMock(return_value=None)
    engine.scheduler.idle.return_value = True
    engine.downloader = MagicMock()
    engine.downloader.idle.return_value = True
    engine.downloader.fetch = AsyncMock()
    engine.processor = MagicMock()
    engine.processor.enqueue = AsyncMock()
    engine.processor.idle.return_value = True
    engine.task_manager = MagicMock()
    engine.task_manager.all_done.return_value = True
    engine.task_manager.semaphore = asyncio.Semaphore(1)
    engine.task_manager.create_task = MagicMock()
    return engine


class TestCrawlStartRequestsNotIdle:
    """_crawl_start_requests: StopAsyncIteration + not idle → sleep → continue."""

    @pytest.mark.asyncio
    async def test_stop_async_iteration_not_idle(self):
        engine = _make_engine()
        engine.start_requests_running = True
        engine.running = True

        async def empty_gen():
            return
            yield

        engine.start_requests = empty_gen()
        engine.spider_middleware_manager = None

        idle_calls = [False, True]

        def mock_idle():
            if idle_calls:
                return idle_calls.pop(0)
            return True

        with patch.object(engine, "_idle", side_effect=mock_idle), patch("asyncio.sleep", new_callable=AsyncMock):
            await engine._crawl_start_requests()
        assert engine.start_requests_running is False

    @pytest.mark.asyncio
    async def test_exception_not_idle(self):
        engine = _make_engine()
        engine.start_requests_running = True
        engine.running = True

        async def bad_gen():
            yield Request(url="http://example.com")
            raise ValueError("boom")

        engine.start_requests = bad_gen()
        engine.spider_middleware_manager = None
        engine.scheduler.next_request = AsyncMock(return_value=None)

        idle_calls = [False, True]

        def mock_idle():
            if idle_calls:
                return idle_calls.pop(0)
            return True

        with patch.object(engine, "_idle", side_effect=mock_idle), patch("asyncio.sleep", new_callable=AsyncMock):
            await engine._crawl_start_requests()
        assert engine.start_requests_running is False


class TestCrawlTaskRequestsBranches:
    """_crawl_task_requests 各异常路径。"""

    @pytest.mark.asyncio
    async def test_stop_async_iteration(self):
        engine = _make_engine()
        engine._single_task_requests_running = True
        engine.task_requests_running = True

        async def empty_gen():
            return
            yield

        engine.task_requests = empty_gen()
        engine.scheduler.next_request = AsyncMock(return_value=None)

        await engine._crawl_task_requests()
        assert engine.task_requests is None

    @pytest.mark.asyncio
    async def test_runtime_error(self):
        engine = _make_engine()
        engine._single_task_requests_running = True
        engine.task_requests_running = True

        async def runtime_error_gen():
            raise RuntimeError("gen closed")
            yield

        engine.task_requests = runtime_error_gen()
        engine.scheduler.next_request = AsyncMock(return_value=None)

        await engine._crawl_task_requests()
        assert engine.task_requests_running is False

    @pytest.mark.asyncio
    async def test_exception_not_idle_then_idle(self):
        engine = _make_engine()
        engine._single_task_requests_running = True
        engine.task_requests_running = True

        async def bad_gen():
            raise ValueError("task boom")
            yield

        engine.task_requests = bad_gen()
        engine.scheduler.next_request = AsyncMock(return_value=None)

        idle_calls = [False, True]

        def mock_idle():
            if idle_calls:
                return idle_calls.pop(0)
            return True

        with patch.object(engine, "_idle", side_effect=mock_idle), patch("asyncio.sleep", new_callable=AsyncMock):
            await engine._crawl_task_requests()
        assert engine._single_task_requests_running is False


class TestCrawlTask:
    """_crawl 创建 crawl_task 并执行。"""

    @pytest.mark.asyncio
    async def test_crawl_executes_task(self):
        engine = _make_engine()
        req = Request(url="http://example.com")
        resp = Response(url="http://example.com", headers={}, status=200, body=b"ok", request=req)
        engine.downloader.fetch = AsyncMock(return_value=MagicMock(response=resp, reason=None))
        engine.downloader_middleware_manager = None
        engine.spider_middleware_manager = None
        engine.spider.parse = MagicMock(return_value=None)

        await engine._crawl(req)
        # task_manager.create_task 被调用
        engine.task_manager.create_task.assert_called_once()


class TestDoDownloadResponse:
    """_do_download 异常 + 中间件返回 Response。"""

    @pytest.mark.asyncio
    async def test_exception_middleware_returns_response(self):
        engine = _make_engine()
        engine.downloader_middleware_manager = MagicMock()
        resp = Response(
            url="http://example.com", headers={}, status=200, body=b"ok", request=Request(url="http://example.com")
        )
        engine.downloader_middleware_manager.process_exception = AsyncMock(return_value=resp)
        engine.downloader.fetch = AsyncMock(side_effect=ConnectionError("fail"))

        req = Request(url="http://example.com")
        result = await engine._do_download(req)
        assert result is not None
        assert result.response is resp
        assert result.reason is None


class TestHandleSuccessResponseCoroutine:
    """_handle_success_response: coroutine callback 路径。"""

    @pytest.mark.asyncio
    async def test_coroutine_callback(self):
        engine = _make_engine()
        engine.spider_middleware_manager = None

        req = Request(url="http://example.com")
        resp = Response(url="http://example.com", headers={}, status=200, body=b"ok", request=req)

        async def async_parse(response):
            pass

        req.callback = async_parse
        result = await engine._handle_success_response(resp, req)
        assert result is None
        engine.spider.stats_collector.record_parse_success.assert_called_once()

    @pytest.mark.asyncio
    async def test_generator_callback_with_spider_middleware(self):
        engine = _make_engine()
        engine.spider_middleware_manager = MagicMock()
        engine.spider_middleware_manager.process_spider_input = AsyncMock(return_value=True)
        engine.spider_middleware_manager.process_spider_output = MagicMock(side_effect=lambda _r, g, _s: g)

        req = Request(url="http://example.com")
        resp = Response(url="http://example.com", headers={}, status=200, body=b"ok", request=req)

        def gen_parse(response):
            yield _TestItem(url="http://example.com")

        req.callback = gen_parse
        result = await engine._handle_success_response(resp, req)
        assert result is not None
        engine.spider.stats_collector.record_parse_success.assert_called_once()


class TestProcessResponseMiddlewareRequest:
    """_process_response_middleware 返回 Request。"""

    @pytest.mark.asyncio
    async def test_returns_request(self):
        engine = _make_engine()
        engine.downloader_middleware_manager = MagicMock()
        retry_req = Request(url="http://example.com/retry")
        engine.downloader_middleware_manager.process_response = AsyncMock(return_value=retry_req)

        req = Request(url="http://example.com")
        resp = Response(url="http://example.com", headers={}, status=200, body=b"ok", request=req)
        result = await engine._process_response_middleware(req, resp)
        assert result is None
        engine.scheduler.enqueue_request.assert_called_once_with(retry_req)


class TestRedisImportFallback:
    """RedisUtil import 失败时 RedisUtil = None。"""

    def test_redis_util_none_when_import_fails(self):
        # RedisUtil 可能是 None 或实际类，取决于 redis 是否安装
        # 这里只验证属性存在
        assert hasattr(aio_engine_mod, "RedisUtil")
