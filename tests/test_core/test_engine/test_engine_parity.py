"""引擎对等测试：相同场景穿过 AioEngine 和 SyncEngine，断言可观测行为一致。

这组测试是"漂移防火墙"——如果有人在 sync 侧修了 bug 但忘了 aio（或反之），
对应的对等测试会变红。每个场景用 mock 组件隔离执行模型差异，只验证
引擎自身的调度/分派/状态机逻辑是否一致。
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from maize.common.http.request import Request
from maize.common.http.response import Response
from maize.common.items import Item
from maize.common.items.field import Field
from maize.common.model.download_response_model import DownloadResponse
from maize.core.engine.aio_engine import AioEngine
from maize.exceptions.spider_exception import OutputException
from maize.settings import SpiderSettings
from maize.sync.classic.engine.sync_engine import SyncEngine


class _ParityItem(Item):
    url: str = Field()


def _resp(url: str = "http://x", status: int = 200) -> Response:
    """构造一个最小可用的 Response，避免每个测试重复必填参数。"""
    return Response(url=url, headers={}, request=Request(url=url), status=status)


# ---------------------------------------------------------------------------
# Engine factory helpers
# ---------------------------------------------------------------------------


def _make_aio_engine() -> AioEngine:
    crawler = MagicMock()
    crawler.settings = SpiderSettings()
    crawler.idle.return_value = True
    engine = AioEngine(crawler)
    engine.spider = MagicMock()
    engine.spider.gte_priority = None
    engine.spider.stats_collector.record_download_success = AsyncMock()
    engine.spider.stats_collector.record_download_fail = AsyncMock()
    engine.spider.stats_collector.record_parse_success = AsyncMock()
    engine.spider.stats_collector.record_parse_fail = AsyncMock()
    engine.scheduler = MagicMock()
    engine.scheduler.put = AsyncMock()
    engine.scheduler.get = AsyncMock(return_value=None)
    engine.scheduler.get_by_priority = AsyncMock(return_value=None)
    engine.scheduler.qsize.return_value = 0
    engine.downloader = MagicMock()
    engine.downloader.idle.return_value = True
    engine.downloader.fetch = AsyncMock()
    engine.processor = MagicMock()
    engine.processor.enqueue = AsyncMock()
    engine.processor.idle.return_value = True
    engine.task_manager = MagicMock()
    engine.task_manager.all_done.return_value = True
    engine.task_manager.semaphore = MagicMock()
    engine.task_manager.semaphore.acquire = AsyncMock()
    engine.task_manager.create_task = MagicMock()
    return engine


def _make_sync_engine() -> SyncEngine:
    crawler = MagicMock()
    crawler.settings = SpiderSettings()
    crawler.idle.return_value = True
    engine = SyncEngine(crawler)
    engine.spider = MagicMock()
    engine.spider.gte_priority = None
    engine.spider.stats_collector = MagicMock()
    engine.scheduler = MagicMock()
    engine.scheduler.put = MagicMock()
    engine.scheduler.get = MagicMock(return_value=None)
    engine.scheduler.get_by_priority = MagicMock(return_value=None)
    engine.scheduler.qsize.return_value = 0
    engine.downloader = MagicMock()
    engine.downloader.idle.return_value = True
    engine.downloader.fetch = MagicMock()
    engine.processor = MagicMock()
    engine.processor.enqueue = MagicMock()
    engine.processor.idle.return_value = True
    engine.task_manager = MagicMock()
    engine.task_manager.all_done.return_value = True
    engine.task_manager.semaphore = MagicMock()
    engine.task_manager.create_task = MagicMock()
    return engine


# ---------------------------------------------------------------------------
# Parity scenarios
# ---------------------------------------------------------------------------


class TestFetchMiddlewareShortCircuitResponse:
    """中间件返回 Response → 跳过下载，直接走 success handler。"""

    @pytest.mark.asyncio
    async def test_aio(self):
        engine = _make_aio_engine()
        engine.downloader_middleware_manager = MagicMock()
        engine.downloader_middleware_manager.process_request = AsyncMock(return_value=_resp(status=200))
        engine.spider_middleware_manager = MagicMock()
        engine.spider_middleware_manager.process_spider_input = AsyncMock(return_value=True)

        result = await engine._fetch(Request(url="http://x"))
        assert result is not None
        engine.downloader.fetch.assert_not_called()

    def test_sync(self):
        engine = _make_sync_engine()
        engine.downloader_middleware_manager = MagicMock()
        engine.downloader_middleware_manager.process_request = MagicMock(return_value=_resp(status=200))
        engine.spider_middleware_manager = MagicMock()
        engine.spider_middleware_manager.process_spider_input = MagicMock(return_value=True)

        result = engine._fetch(Request(url="http://x"))
        assert result is not None
        engine.downloader.fetch.assert_not_called()


class TestFetchMiddlewareDropsRequest:
    """中间件返回 None → 丢弃请求，返回 None。"""

    @pytest.mark.asyncio
    async def test_aio(self):
        engine = _make_aio_engine()
        engine.downloader_middleware_manager = MagicMock()
        engine.downloader_middleware_manager.process_request = AsyncMock(return_value=None)

        result = await engine._fetch(Request(url="http://x"))
        assert result is None
        engine.downloader.fetch.assert_not_called()

    def test_sync(self):
        engine = _make_sync_engine()
        engine.downloader_middleware_manager = MagicMock()
        engine.downloader_middleware_manager.process_request = MagicMock(return_value=None)

        result = engine._fetch(Request(url="http://x"))
        assert result is None
        engine.downloader.fetch.assert_not_called()


class TestFetchDownloadFailNoResponse:
    """下载结果 response=None → 记录失败 + 走 error handler。"""

    @pytest.mark.asyncio
    async def test_aio(self):
        engine = _make_aio_engine()
        engine.downloader_middleware_manager = MagicMock()
        engine.downloader_middleware_manager.process_request = AsyncMock(return_value=Request(url="http://x"))
        engine.downloader_middleware_manager.process_response = AsyncMock()
        engine.downloader.fetch = AsyncMock(return_value=DownloadResponse(response=None, reason="timeout"))
        result = await engine._fetch(Request(url="http://x"))
        assert result is None
        engine.spider.stats_collector.record_download_fail.assert_called_once_with("timeout")

    def test_sync(self):
        engine = _make_sync_engine()
        engine.downloader_middleware_manager = MagicMock()
        engine.downloader_middleware_manager.process_request = MagicMock(return_value=Request(url="http://x"))
        engine.downloader_middleware_manager.process_response = MagicMock()
        engine.downloader.fetch = MagicMock(return_value=DownloadResponse(response=None, reason="timeout"))
        result = engine._fetch(Request(url="http://x"))
        assert result is None
        engine.spider.stats_collector.record_download_fail.assert_called_once_with("timeout")


class TestDoDownloadExceptionMiddlewareReturnsRequest:
    """下载异常 + 中间件返回 Request → 重新入队，返回 None。"""

    @pytest.mark.asyncio
    async def test_aio(self):
        engine = _make_aio_engine()
        engine.downloader_middleware_manager = MagicMock()
        retry_req = Request(url="http://retry")
        engine.downloader_middleware_manager.process_exception = AsyncMock(return_value=retry_req)
        engine.downloader.fetch = AsyncMock(side_effect=ConnectionError("boom"))

        result = await engine._do_download(Request(url="http://x"))
        assert result is None
        engine.scheduler.put.assert_called_once_with(retry_req)

    def test_sync(self):
        engine = _make_sync_engine()
        engine.downloader_middleware_manager = MagicMock()
        retry_req = Request(url="http://retry")
        engine.downloader_middleware_manager.process_exception = MagicMock(return_value=retry_req)
        engine.downloader.fetch = MagicMock(side_effect=ConnectionError("boom"))

        result = engine._do_download(Request(url="http://x"))
        assert result is None
        engine.scheduler.put.assert_called_once_with(retry_req)


class TestDoDownloadExceptionMiddlewareReturnsResponse:
    """下载异常 + 中间件返回 Response → 构造 DownloadResponse，response 非空。"""

    @pytest.mark.asyncio
    async def test_aio(self):
        engine = _make_aio_engine()
        engine.downloader_middleware_manager = MagicMock()
        resp = _resp(status=200)
        engine.downloader_middleware_manager.process_exception = AsyncMock(return_value=resp)
        engine.downloader.fetch = AsyncMock(side_effect=ConnectionError("boom"))

        result = await engine._do_download(Request(url="http://x"))
        assert result is not None
        assert result.response is resp
        assert result.reason is None

    def test_sync(self):
        engine = _make_sync_engine()
        engine.downloader_middleware_manager = MagicMock()
        resp = _resp(status=200)
        engine.downloader_middleware_manager.process_exception = MagicMock(return_value=resp)
        engine.downloader.fetch = MagicMock(side_effect=ConnectionError("boom"))

        result = engine._do_download(Request(url="http://x"))
        assert result is not None
        assert result.response is resp
        assert result.reason is None


class TestDoDownloadExceptionNoMiddleware:
    """下载异常 + 无中间件 → 重新抛出。"""

    @pytest.mark.asyncio
    async def test_aio(self):
        engine = _make_aio_engine()
        engine.downloader_middleware_manager = None
        engine.downloader.fetch = AsyncMock(side_effect=ConnectionError("boom"))

        with pytest.raises(ConnectionError):
            await engine._do_download(Request(url="http://x"))

    def test_sync(self):
        engine = _make_sync_engine()
        engine.downloader_middleware_manager = None
        engine.downloader.fetch = MagicMock(side_effect=ConnectionError("boom"))

        with pytest.raises(ConnectionError):
            engine._do_download(Request(url="http://x"))


class TestHandleSuccessResponseCallbackYieldsItems:
    """回调 yield Item → 记录 parse 成功 + 返回生成器。"""

    @pytest.mark.asyncio
    async def test_aio(self):
        engine = _make_aio_engine()
        engine.spider_middleware_manager = None
        engine.spider.parse = MagicMock(return_value=iter([_ParityItem(url="http://r")]))

        result = await engine._handle_success_response(_resp(status=200), Request(url="http://x"))
        assert result is not None
        engine.spider.stats_collector.record_parse_success.assert_called_once()

    def test_sync(self):
        engine = _make_sync_engine()
        engine.spider_middleware_manager = None
        engine.spider.parse = MagicMock(return_value=iter([_ParityItem(url="http://r")]))

        result = engine._handle_success_response(_resp(status=200), Request(url="http://x"))
        assert result is not None
        engine.spider.stats_collector.record_parse_success.assert_called_once()


class TestHandleSuccessResponseCallbackException:
    """回调抛异常 → 记录 parse 失败 + 返回 None。"""

    @pytest.mark.asyncio
    async def test_aio(self):
        engine = _make_aio_engine()
        engine.spider_middleware_manager = None

        def bad_callback(response):
            raise ValueError("parse boom")

        engine.spider.parse = bad_callback

        result = await engine._handle_success_response(_resp(status=200), Request(url="http://x"))
        assert result is None
        engine.spider.stats_collector.record_parse_fail.assert_called_once()

    def test_sync(self):
        engine = _make_sync_engine()
        engine.spider_middleware_manager = None

        def bad_callback(response):
            raise ValueError("parse boom")

        engine.spider.parse = bad_callback

        result = engine._handle_success_response(_resp(status=200), Request(url="http://x"))
        assert result is None
        engine.spider.stats_collector.record_parse_fail.assert_called_once()


class TestHandleSpiderOutput:
    """_handle_spider_output: Request 和 Item → 都 enqueue 到 processor。"""

    @pytest.mark.asyncio
    async def test_aio(self):
        engine = _make_aio_engine()

        async def gen():
            yield Request(url="http://a")
            yield _ParityItem(url="http://b")

        await engine._handle_spider_output(gen())
        assert engine.processor.enqueue.call_count == 2

    def test_sync(self):
        engine = _make_sync_engine()

        def gen():
            yield Request(url="http://a")
            yield _ParityItem(url="http://b")

        engine._handle_spider_output(gen())
        assert engine.processor.enqueue.call_count == 2


class TestHandleSpiderOutputInvalidType:
    """_handle_spider_output: 非 Request/Item → OutputException。"""

    @pytest.mark.asyncio
    async def test_aio(self):
        engine = _make_aio_engine()

        async def gen():
            yield "not a valid output"

        with pytest.raises(OutputException):
            await engine._handle_spider_output(gen())

    def test_sync(self):
        engine = _make_sync_engine()

        def gen():
            yield "not a valid output"

        with pytest.raises(OutputException):
            engine._handle_spider_output(gen())


class TestIdleCheck:
    """_idle: 所有组件空闲 → True；任一忙 → False。"""

    @pytest.mark.asyncio
    async def test_aio_all_idle(self):
        engine = _make_aio_engine()
        assert engine._idle() is True

    def test_sync_all_idle(self):
        engine = _make_sync_engine()
        assert engine._idle() is True

    @pytest.mark.asyncio
    async def test_aio_scheduler_busy(self):
        engine = _make_aio_engine()
        engine.scheduler.qsize.return_value = 1
        assert engine._idle() is False

    def test_sync_scheduler_busy(self):
        engine = _make_sync_engine()
        engine.scheduler.qsize.return_value = 1
        assert engine._idle() is False


class TestCrawlTaskRequestsStopIteration:
    """_crawl_task_requests: StopIteration → 正确重置所有标志位。

    这是 bug #9 的回归测试——aio 侧曾漏重置 _single_task_requests_running
    和 task_requests_running，导致无限循环。
    """

    @pytest.mark.asyncio
    async def test_aio(self):
        engine = _make_aio_engine()
        engine._single_task_requests_running = True
        engine.task_requests_running = True

        async def empty_gen():
            return
            yield

        engine.task_requests = empty_gen()
        engine.scheduler.get = AsyncMock(return_value=None)
        engine.scheduler.get_by_priority = AsyncMock(return_value=None)

        await engine._crawl_task_requests()
        assert engine.task_requests is None
        assert engine._single_task_requests_running is False
        assert engine.task_requests_running is False

    def test_sync(self):
        engine = _make_sync_engine()
        engine._single_task_requests_running = True
        engine.task_requests_running = True

        def empty_gen():
            return
            yield

        engine.task_requests = empty_gen()
        engine.scheduler.get = MagicMock(return_value=None)
        engine.scheduler.get_by_priority = MagicMock(return_value=None)

        engine._crawl_task_requests()
        assert engine.task_requests is None
        assert engine._single_task_requests_running is False
        assert engine.task_requests_running is False
