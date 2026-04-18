"""
Tests for Processor
"""

from asyncio import QueueEmpty
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from maize.common.http.request import Request
from maize.common.items import Item
from maize.core.processor.processor import Processor


class TestProcessor:
    """Test Processor"""

    @pytest.fixture
    def mock_crawler(self):
        crawler = MagicMock()
        crawler.settings = MagicMock()
        crawler.settings.middleware = MagicMock()
        crawler.settings.middleware.pipeline_middlewares = {}
        crawler.spider = MagicMock()
        crawler.spider.stats_collector = MagicMock()
        crawler.spider.stats_collector.record_pipeline_success = AsyncMock()
        crawler.spider.stats_collector.record_pipeline_fail = AsyncMock()
        return crawler

    @pytest.fixture
    def processor(self, mock_crawler):
        with patch("maize.core.processor.processor.get_logger"):
            proc = Processor(mock_crawler)
            proc.pipeline_scheduler = MagicMock()
            proc.pipeline_scheduler.process = AsyncMock()
            return proc

    @pytest.mark.asyncio
    async def test_open(self, processor, mock_crawler):
        """Test open method"""
        processor.pipeline_middleware_manager = MagicMock()
        processor.pipeline_middleware_manager.open = AsyncMock()
        processor.pipeline_scheduler = MagicMock()
        processor.pipeline_scheduler.open = AsyncMock()

        await processor.open()

        processor.pipeline_middleware_manager.open.assert_called_once()
        processor.pipeline_scheduler.open.assert_called_once()

    @pytest.mark.asyncio
    async def test_close(self, processor, mock_crawler):
        """Test close method"""
        processor.pipeline_middleware_manager = MagicMock()
        processor.pipeline_middleware_manager.close = AsyncMock()
        processor.pipeline_scheduler = MagicMock()

        close_result = MagicMock()
        close_result.success_count = 5
        close_result.fail_count = 2
        processor.pipeline_scheduler.close = AsyncMock(return_value=close_result)

        await processor.close()

        mock_crawler.spider.stats_collector.record_pipeline_success.assert_called_once_with(5)
        mock_crawler.spider.stats_collector.record_pipeline_fail.assert_called_once_with(2)
        processor.pipeline_middleware_manager.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_enqueue_request(self, processor, mock_crawler):
        """Test enqueue with Request"""
        processor.queue = MagicMock()
        processor.queue.put = AsyncMock()
        processor.process = AsyncMock()
        processor.crawler.engine = MagicMock()
        processor.crawler.engine.enqueue_request = AsyncMock()

        request = Request(url="https://example.com")

        await processor.enqueue(request)

        processor.queue.put.assert_called_once_with(request)
        processor.process.assert_called_once()

    @pytest.mark.asyncio
    async def test_enqueue_item(self, processor, mock_crawler):
        """Test enqueue with Item"""
        processor.queue = MagicMock()
        processor.queue.put = AsyncMock()
        processor.process = AsyncMock()

        item = Item()

        await processor.enqueue(item)

        processor.queue.put.assert_called_once_with(item)
        processor.process.assert_called_once()

    @pytest.mark.asyncio
    async def test_idle_when_empty(self, processor):
        """Test idle when queue is empty"""
        processor.queue = MagicMock()
        processor.queue.qsize = MagicMock(return_value=0)

        assert processor.idle() is True

    @pytest.mark.asyncio
    async def test_idle_when_not_empty(self, processor):
        """Test idle when queue is not empty"""
        processor.queue = MagicMock()
        processor.queue.qsize = MagicMock(return_value=5)

        assert processor.idle() is False

    def test_len(self, processor):
        """Test __len__ method"""
        processor.queue = MagicMock()
        processor.queue.qsize = MagicMock(return_value=3)

        assert len(processor) == 3

    @pytest.mark.asyncio
    async def test_process_with_item(self, processor, mock_crawler):
        """Test process with Item"""
        processor.pipeline_middleware_manager = MagicMock()
        processor.pipeline_middleware_manager.process_item_before = AsyncMock(return_value=MagicMock())
        processor.pipeline_middleware_manager.process_item_after = AsyncMock()

        process_result = MagicMock()
        process_result.success_count = 1
        process_result.fail_count = 0
        processor.pipeline_scheduler.process = AsyncMock(return_value=process_result)

        # Set queue with an item
        item = Item()
        processor.queue = MagicMock()
        processor.queue.get = AsyncMock(side_effect=[item, QueueEmpty()])
        processor.queue.qsize = MagicMock(side_effect=[1, 0])

        processor.logger = MagicMock()

        await processor.process()

        processor.pipeline_middleware_manager.process_item_before.assert_called_once()
        processor.pipeline_scheduler.process.assert_called_once()
        processor.pipeline_middleware_manager.process_item_after.assert_called_once()
        mock_crawler.spider.stats_collector.record_pipeline_success.assert_called_once_with(1)
        mock_crawler.spider.stats_collector.record_pipeline_fail.assert_called_once_with(0)

    @pytest.mark.asyncio
    async def test_process_with_request(self, processor, mock_crawler):
        """Test process with Request"""
        processor.pipeline_middleware_manager = MagicMock()

        request = Request(url="https://example.com")
        processor.queue = MagicMock()
        processor.queue.get = AsyncMock(side_effect=[request, QueueEmpty()])
        processor.queue.qsize = MagicMock(side_effect=[1, 0])

        processor.crawler.engine = MagicMock()
        processor.crawler.engine.enqueue_request = AsyncMock()

        processor.logger = MagicMock()

        await processor.process()

        processor.crawler.engine.enqueue_request.assert_called_once_with(request)
        processor.pipeline_middleware_manager.process_item_before.assert_not_called()
        processor.pipeline_scheduler.process.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_item_dropped_by_middleware(self, processor, mock_crawler):
        """Test process when item is dropped by middleware"""
        processor.pipeline_middleware_manager = MagicMock()
        processor.pipeline_middleware_manager.process_item_before = AsyncMock(return_value=None)

        item = Item()
        processor.queue = MagicMock()
        processor.queue.get = AsyncMock(side_effect=[item, QueueEmpty()])
        processor.queue.qsize = MagicMock(side_effect=[1, 0])

        processor.logger = MagicMock()

        await processor.process()

        processor.pipeline_middleware_manager.process_item_before.assert_called_once()
        processor.pipeline_scheduler.process.assert_not_called()
        processor.logger.debug.assert_called()
