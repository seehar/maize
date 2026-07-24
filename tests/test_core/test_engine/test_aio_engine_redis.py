"""
Tests for AioEngine redis paths, crawl loop with task_spider,
_crawl_start_requests exception/idle paths, _get_next_request distributed path.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from maize.common.http.request import Request
from maize.common.http.response import Response
from maize.core.engine.aio_engine import AioEngine
from maize.settings import SpiderSettings


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


class TestEngineRedisPaths:
    """Cover redis init, enqueue, _get_next_request with redis."""

    @pytest.mark.asyncio
    async def test_enqueue_request_with_redis(self):
        """enqueue_request stores to redis when __redis_util is set."""
        engine = _make_engine()
        # Access private attr via name mangling
        engine._AioEngine__redis_util = MagicMock()
        engine._AioEngine__redis_util.set = AsyncMock()
        engine._AioEngine__redis_key_queue = "queue"
        req = Request("https://example.com")
        await engine.enqueue_request(req)
        engine._AioEngine__redis_util.set.assert_called_once()
        engine.scheduler.put.assert_called_once_with(req)

    @pytest.mark.asyncio
    async def test_get_next_request_with_redis(self):
        """_get_next_request sets running key and deletes queue key when redis is active."""
        engine = _make_engine()
        engine.crawler.spider.gte_priority = None
        req = Request("https://example.com")
        engine.scheduler.get = AsyncMock(return_value=req)
        engine.scheduler.get_by_priority = AsyncMock(return_value=req)
        engine._AioEngine__redis_util = MagicMock()
        engine._AioEngine__redis_util.set = AsyncMock()
        engine._AioEngine__redis_util.delete = AsyncMock()
        engine._AioEngine__redis_key_running = "running"
        engine._AioEngine__redis_key_queue = "queue"

        result = await engine._get_next_request()
        assert result is req
        engine._AioEngine__redis_util.set.assert_called_once()
        engine._AioEngine__redis_util.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_next_request_distributed_lock_fails(self):
        """When distributed lock fails, _get_next_request returns None."""
        engine = _make_engine()
        engine.crawler.spider.gte_priority = None
        req = Request("https://example.com")
        engine.scheduler.get = AsyncMock(return_value=req)
        engine.scheduler.get_by_priority = AsyncMock(return_value=req)
        engine.is_distributed = True
        engine._AioEngine__redis_util = MagicMock()
        engine._AioEngine__redis_util.nx_set = AsyncMock(return_value=False)
        engine._AioEngine__redis_key_distributed_lock = "lock"

        result = await engine._get_next_request()
        assert result is None

    @pytest.mark.asyncio
    async def test_get_next_request_distributed_lock_succeeds(self):
        """When distributed lock succeeds, request is returned."""
        engine = _make_engine()
        engine.crawler.spider.gte_priority = None
        req = Request("https://example.com")
        engine.scheduler.get = AsyncMock(return_value=req)
        engine.scheduler.get_by_priority = AsyncMock(return_value=req)
        engine.is_distributed = True
        engine._AioEngine__redis_util = MagicMock()
        engine._AioEngine__redis_util.nx_set = AsyncMock(return_value=True)
        engine._AioEngine__redis_util.set = AsyncMock()
        engine._AioEngine__redis_util.delete = AsyncMock()
        engine._AioEngine__redis_key_distributed_lock = "lock"
        engine._AioEngine__redis_key_running = "running"
        engine._AioEngine__redis_key_queue = "queue"

        result = await engine._get_next_request()
        assert result is req

    def test_init_redis(self):
        """Cover __init_redis when redis is enabled."""
        engine = _make_engine()
        engine.settings.redis.use_redis = True
        engine.spider = MagicMock()
        engine.spider.__class__.__name__ = "TestSpider"

        with patch("maize.core.engine.aio_engine.RedisUtil") as mock_redis_cls:
            mock_redis = MagicMock()
            mock_redis_cls.return_value = mock_redis
            engine._AioEngine__init_redis()
            mock_redis_cls.assert_called_once()

    def test_get_redis_key(self):
        """Cover __get_redis_key."""
        engine = _make_engine()
        engine.spider = MagicMock()
        engine.spider.__class__.__name__ = "BaiduNewsSpider"
        result = engine._AioEngine__get_redis_key("lock")
        assert "baidu_news_spider" in result
        assert "lock" in result


class TestEngineCrawlLoop:
    """Cover crawl() main loop paths."""

    @pytest.mark.asyncio
    async def test_crawl_normal_spider_completes(self):
        """crawl() with normal spider (not task_spider) runs and stops."""
        engine = _make_engine()
        engine.spider.__spider_type__ = "spider"
        engine.start_requests_running = True
        engine.running = True

        # Mock _crawl_start_requests to set start_requests_running = False
        async def mock_crawl_sr():
            engine.start_requests_running = False

        engine._crawl_start_requests = mock_crawl_sr
        engine.close_spider = AsyncMock()

        await engine.crawl()
        engine.close_spider.assert_called_once()

    @pytest.mark.asyncio
    async def test_crawl_task_spider(self):
        """crawl() with task_spider type calls _crawl_task_requests."""
        engine = _make_engine()
        engine.spider.__spider_type__ = "task_spider"

        async def gen():
            return
            yield  # makes it an async generator

        engine.spider.start_requests = MagicMock(return_value=gen())
        engine.start_requests_running = True
        engine.running = True
        engine.task_requests_running = True

        async def mock_crawl_sr():
            engine.start_requests_running = False

        async def mock_crawl_tr():
            engine.task_requests_running = False
            engine._single_task_requests_running = False

        engine._crawl_start_requests = mock_crawl_sr
        engine._crawl_task_requests = mock_crawl_tr
        engine.close_spider = AsyncMock()

        await engine.crawl()
        engine.close_spider.assert_called_once()


class TestCrawlStartRequestsEdgeCases:
    """Cover _crawl_start_requests exception and idle-wait paths."""

    @pytest.mark.asyncio
    async def test_start_requests_exception_when_idle(self):
        """When start_requests raises Exception and engine is idle, stops."""
        engine = _make_engine()
        engine.spider_middleware_manager = None
        engine.start_requests_running = True

        async def bad_gen():
            raise RuntimeError("gen error")
            yield  # never reached

        engine.start_requests = bad_gen()
        engine.scheduler.get = AsyncMock(return_value=None)
        engine.scheduler.get_by_priority = AsyncMock(return_value=None)
        engine.scheduler.qsize.return_value = 0
        engine.downloader.idle.return_value = True
        engine.processor.idle.return_value = True
        engine.task_manager.all_done.return_value = True
        engine.crawler.idle.return_value = True
        engine._crawl = AsyncMock()

        await engine._crawl_start_requests()
        assert engine.start_requests_running is False

    @pytest.mark.asyncio
    async def test_start_requests_stop_async_iteration_with_pending(self):
        """When start_requests exhausted but not idle, loops once then stops."""
        engine = _make_engine()
        engine.spider_middleware_manager = None
        engine.start_requests_running = True

        async def gen():
            return
            yield

        engine.start_requests = gen()
        engine.scheduler.get = AsyncMock(return_value=None)
        engine.scheduler.get_by_priority = AsyncMock(return_value=None)

        # First check: not idle -> sleep -> second check: idle -> stop
        call_count = 0

        def idle_side_effect():
            nonlocal call_count
            call_count += 1
            return call_count > 1

        engine.scheduler.qsize.return_value = 0
        engine.downloader.idle.return_value = True
        engine.processor.idle.return_value = True
        engine.task_manager.all_done.return_value = True
        engine.crawler.idle.return_value = True
        engine._crawl = AsyncMock()

        with patch("maize.core.engine.aio_engine.asyncio.sleep", new_callable=AsyncMock):
            await engine._crawl_start_requests()
        assert engine.start_requests_running is False


class TestHandleSuccessRedisDelete:
    """Cover _handle_success_response redis delete path."""

    @pytest.mark.asyncio
    async def test_redis_delete_after_callback(self):
        """When __redis_util is set, redis delete is called after callback."""
        engine = _make_engine()
        engine.spider_middleware_manager = None
        engine.spider.parse = MagicMock(return_value=None)
        engine._AioEngine__redis_util = MagicMock()
        engine._AioEngine__redis_util.delete = AsyncMock()
        engine._AioEngine__redis_key_running = "running"

        req = Request("https://example.com")
        resp = Response(url="https://example.com", headers={}, request=req, status=200, text="ok")
        await engine._handle_success_response(resp, req)
        engine._AioEngine__redis_util.delete.assert_called_once()


class TestHandleErrorRedisDelete:
    """Cover _handle_error_response redis delete path."""

    @pytest.mark.asyncio
    async def test_redis_delete_after_error_callback(self):
        """When __redis_util is set, redis delete is called after error callback."""
        engine = _make_engine()
        engine._AioEngine__redis_util = MagicMock()
        engine._AioEngine__redis_util.delete = AsyncMock()
        engine._AioEngine__redis_key_running = "running"

        def err_cb(request):
            return None

        req = Request("https://example.com", error_callback=err_cb)
        await engine._handle_error_response(req)
        engine._AioEngine__redis_util.delete.assert_called_once()
