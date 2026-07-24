"""
Tests for AioEngine helper methods: _idle, _get_downloader, _handle_spider_output.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from maize.base.downloader.base_downloader import BaseDownloader
from maize.common.http.request import Request
from maize.common.items import Item
from maize.core.engine.aio_engine import AioEngine
from maize.exceptions.spider_exception import OutputException, StartRequestsNotImplementedException
from maize.settings import SpiderSettings


def _make_crawler():
    crawler = MagicMock()
    crawler.settings = SpiderSettings()
    crawler.idle.return_value = True
    return crawler


class TestAioEngineGetDownloader:
    """Test AioEngine._get_downloader."""

    def test_get_downloader_returns_class(self):
        crawler = _make_crawler()
        crawler.settings.downloader = "maize.AioHttpDownloader"
        engine = AioEngine(crawler)
        dl_cls = engine._get_downloader()
        assert issubclass(dl_cls, BaseDownloader)

    def test_get_downloader_invalid_class_raises_type_error(self):
        crawler = _make_crawler()
        crawler.settings.downloader = "maize.utils.log_util.get_logger"
        engine = AioEngine(crawler)
        with pytest.raises(TypeError, match="does not fully implement"):
            engine._get_downloader()


class TestAioEngineIdle:
    """Test AioEngine._idle."""

    def test_idle_all_idle(self):
        crawler = _make_crawler()
        engine = AioEngine(crawler)
        engine.scheduler = MagicMock()
        engine.scheduler.qsize.return_value = 0
        engine.downloader = MagicMock()
        engine.downloader.idle.return_value = True
        engine.processor = MagicMock()
        engine.processor.idle.return_value = True
        engine.task_manager = MagicMock()
        engine.task_manager.all_done.return_value = True

        assert engine._idle() is True

    def test_idle_scheduler_busy(self):
        crawler = _make_crawler()
        engine = AioEngine(crawler)
        engine.scheduler = MagicMock()
        engine.scheduler.qsize.return_value = 1
        engine.downloader = MagicMock()
        engine.downloader.idle.return_value = True
        engine.processor = MagicMock()
        engine.processor.idle.return_value = True
        engine.task_manager = MagicMock()
        engine.task_manager.all_done.return_value = True
        crawler.idle.return_value = True

        assert engine._idle() is False

    def test_idle_downloader_busy(self):
        crawler = _make_crawler()
        engine = AioEngine(crawler)
        engine.scheduler = MagicMock()
        engine.scheduler.qsize.return_value = 0
        engine.downloader = MagicMock()
        engine.downloader.idle.return_value = False
        engine.processor = MagicMock()
        engine.processor.idle.return_value = True
        engine.task_manager = MagicMock()
        engine.task_manager.all_done.return_value = True
        crawler.idle.return_value = True

        assert engine._idle() is False

    def test_idle_crawler_busy(self):
        crawler = _make_crawler()
        engine = AioEngine(crawler)
        engine.scheduler = MagicMock()
        engine.scheduler.qsize.return_value = 0
        engine.downloader = MagicMock()
        engine.downloader.idle.return_value = True
        engine.processor = MagicMock()
        engine.processor.idle.return_value = True
        engine.task_manager = MagicMock()
        engine.task_manager.all_done.return_value = True
        crawler.idle.return_value = False

        assert engine._idle() is False


class TestAioEngineHandleSpiderOutput:
    """Test AioEngine._handle_spider_output."""

    @pytest.mark.asyncio
    async def test_handles_request_output(self):
        crawler = _make_crawler()
        engine = AioEngine(crawler)
        engine.processor = MagicMock()
        engine.processor.enqueue = AsyncMock()

        req = Request("https://example.com")

        async def gen():
            yield req

        await engine._handle_spider_output(gen())
        engine.processor.enqueue.assert_called_once_with(req)

    @pytest.mark.asyncio
    async def test_handles_item_output(self):
        crawler = _make_crawler()
        engine = AioEngine(crawler)
        engine.processor = MagicMock()
        engine.processor.enqueue = AsyncMock()

        item = Item()

        async def gen():
            yield item

        await engine._handle_spider_output(gen())
        engine.processor.enqueue.assert_called_once_with(item)

    @pytest.mark.asyncio
    async def test_raises_on_invalid_output(self):
        crawler = _make_crawler()
        engine = AioEngine(crawler)
        engine.processor = MagicMock()
        engine.processor.enqueue = AsyncMock()

        async def gen():
            yield "not a request or item"

        with pytest.raises(OutputException):
            await engine._handle_spider_output(gen())

    @pytest.mark.asyncio
    async def test_handles_mixed_output(self):
        crawler = _make_crawler()
        engine = AioEngine(crawler)
        engine.processor = MagicMock()
        engine.processor.enqueue = AsyncMock()

        req = Request("https://example.com")
        item = Item()

        async def gen():
            yield req
            yield item

        await engine._handle_spider_output(gen())
        assert engine.processor.enqueue.call_count == 2


class TestAioEngineStartSpider:
    """Test AioEngine.start_spider validation."""

    @pytest.mark.asyncio
    async def test_start_spider_not_implemented_raises(self):
        crawler = _make_crawler()
        engine = AioEngine(crawler)

        class BadSpider:
            __spider_type__ = "spider"

            def start_requests(self):
                raise NotImplementedError

            async def open(self):
                pass

            async def close(self):
                pass

        with pytest.raises(StartRequestsNotImplementedException):
            await engine.start_spider(BadSpider())  # type: ignore[arg-type]
