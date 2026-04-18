"""
Tests for pipeline_scheduler
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from maize.common.model.pipeline_model import PipelineProcessResult
from maize.pipelines.pipeline_scheduler import PipelineScheduler


class TestPipelineScheduler:
    """Test PipelineScheduler"""

    @pytest.fixture
    def mock_settings(self):
        """Create mock settings"""
        settings = MagicMock()
        settings.pipeline.max_cache_count = 100
        settings.pipeline.handle_batch_max_size = 10
        settings.pipeline.handle_interval = 1
        settings.pipeline.error_max_retry_count = 3
        settings.pipeline.error_max_cache_count = 100
        settings.pipeline.error_retry_batch_max_size = 10
        settings.pipeline.error_handle_batch_max_size = 10
        settings.pipeline.error_handle_interval = 1
        settings.pipeline.pipelines = []
        return settings

    @pytest.fixture
    def pipeline_scheduler(self, mock_settings):
        """Create PipelineScheduler"""
        scheduler = PipelineScheduler(mock_settings)
        # Disable logging for tests
        scheduler.logger = MagicMock()
        return scheduler

    def test_init(self, mock_settings):
        """Test scheduler initialization"""
        scheduler = PipelineScheduler(mock_settings)

        assert scheduler.settings == mock_settings
        assert scheduler.item_pipelines == []
        assert scheduler.item_queue.maxsize == 100
        assert scheduler.error_item_queue.maxsize == 100
        assert scheduler.retry_item_queue.maxsize == 100

    def test_len(self, pipeline_scheduler):
        """Test __len__ method"""
        assert len(pipeline_scheduler) == 0

    def test_idle(self, pipeline_scheduler):
        """Test idle method"""
        assert pipeline_scheduler.idle() is True

    def test_error_task_idle(self, pipeline_scheduler):
        """Test error_task_idle method"""
        assert pipeline_scheduler.error_task_idle() is True

    @pytest.mark.asyncio
    async def test_open_no_pipelines(self, pipeline_scheduler):
        """Test open with no pipelines"""
        await pipeline_scheduler.open()
        assert pipeline_scheduler.item_pipelines == []

    @pytest.mark.asyncio
    async def test_open_with_pipelines(self, mock_settings):
        """Test open with pipelines"""
        # Create mock pipeline
        mock_pipeline = MagicMock()
        mock_pipeline.open = AsyncMock()

        scheduler = PipelineScheduler(mock_settings)
        scheduler.logger = MagicMock()  # Disable logging

        with patch("maize.pipelines.pipeline_scheduler.load_class", return_value=lambda _: mock_pipeline):
            mock_settings.pipeline.pipelines = ["mock.pipeline.Path"]
            await scheduler.open()

            mock_pipeline.open.assert_called_once()
            assert len(scheduler.item_pipelines) == 1

    @pytest.mark.asyncio
    async def test_process_item(self, pipeline_scheduler):
        """Test processing an item"""
        # Mock pipeline that returns True
        mock_pipeline = MagicMock()
        mock_pipeline.process_item = AsyncMock(return_value=True)
        pipeline_scheduler.item_pipelines.append(mock_pipeline)

        mock_item = MagicMock()
        mock_item.__retry_count__ = 0

        result = await pipeline_scheduler.process(mock_item)

        assert isinstance(result, PipelineProcessResult)

    @pytest.mark.asyncio
    async def test_process_item_batch(self, pipeline_scheduler):
        """Test processing items in batch"""
        mock_pipeline = MagicMock()
        mock_pipeline.process_item = AsyncMock(return_value=True)
        pipeline_scheduler.item_pipelines.append(mock_pipeline)

        # Add multiple items
        for _i in range(15):
            mock_item = MagicMock()
            mock_item.__retry_count__ = 0
            await pipeline_scheduler.item_queue.put(mock_item)

        # Process batch
        result = await pipeline_scheduler._process_item()

        assert isinstance(result, PipelineProcessResult)

    @pytest.mark.asyncio
    async def test_process_item_with_failure(self, pipeline_scheduler):
        """Test processing item with pipeline failure"""
        mock_pipeline = MagicMock()
        mock_pipeline.process_item = AsyncMock(return_value=False)
        pipeline_scheduler.item_pipelines.append(mock_pipeline)

        mock_item = MagicMock()
        mock_item.__retry_count__ = 0
        mock_item.retry = MagicMock()

        await pipeline_scheduler.item_queue.put(mock_item)

        result = await pipeline_scheduler._process_item()

        assert result.fail_count > 0

    @pytest.mark.asyncio
    async def test_retry_error_items_empty(self, pipeline_scheduler):
        """Test retry error items when queue is empty"""
        result, process_result = await pipeline_scheduler._retry_error_items()

        assert result is False
        assert isinstance(process_result, PipelineProcessResult)

    @pytest.mark.asyncio
    async def test_retry_error_items_with_items(self, pipeline_scheduler):
        """Test retry error items with items in queue"""
        mock_pipeline = MagicMock()
        mock_pipeline.process_item = AsyncMock(return_value=True)
        pipeline_scheduler.item_pipelines.append(mock_pipeline)

        mock_item = MagicMock()
        mock_item.retry = MagicMock()

        await pipeline_scheduler.retry_item_queue.put(mock_item)

        result, _process_result = await pipeline_scheduler._retry_error_items()

        assert result is True

    @pytest.mark.asyncio
    async def test_process_retry_items_empty(self, pipeline_scheduler):
        """Test process_retry_items when queue is empty"""
        result = await pipeline_scheduler.process_retry_items()

        assert isinstance(result, PipelineProcessResult)
        assert result.success_count == 0

    @pytest.mark.asyncio
    async def test_process_error_items_empty(self, pipeline_scheduler):
        """Test process_error_items when queue is empty"""
        await pipeline_scheduler.process_error_items()
        # Should not raise

    @pytest.mark.asyncio
    async def test_single_process_error_items_empty(self, pipeline_scheduler):
        """Test _single_process_error_items when queue is empty"""
        await pipeline_scheduler._single_process_error_items()
        # Should not raise

    @pytest.mark.asyncio
    async def test_single_process_error_items_with_items(self, pipeline_scheduler):
        """Test _single_process_error_items with items"""
        mock_pipeline = MagicMock()
        mock_pipeline.process_error_item = AsyncMock()
        pipeline_scheduler.item_pipelines.append(mock_pipeline)

        mock_item = MagicMock()
        await pipeline_scheduler.error_item_queue.put(mock_item)

        await pipeline_scheduler._single_process_error_items()

        mock_pipeline.process_error_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_enqueue_retry_items_max_retries(self, pipeline_scheduler):
        """Test _enqueue_retry_items when max retries exceeded"""
        pipeline_scheduler.error_item_max_retry_count = 3  # Ensure correct value

        mock_item = MagicMock()
        mock_item.__retry_count__ = 5  # Exceeds max_retry_count (3)

        await pipeline_scheduler._enqueue_retry_items([mock_item])

        # Should be in error queue
        assert not pipeline_scheduler.error_item_queue.empty()

    @pytest.mark.asyncio
    async def test_enqueue_retry_items_under_max_retries(self, pipeline_scheduler):
        """Test _enqueue_retry_items when under max retries"""
        pipeline_scheduler.error_item_max_retry_count = 3  # Ensure correct value

        mock_item = MagicMock()
        mock_item.__retry_count__ = 1  # Under max_retry_count (3)

        await pipeline_scheduler._enqueue_retry_items([mock_item])

        # Should be in retry queue
        assert not pipeline_scheduler.retry_item_queue.empty()

    @pytest.mark.asyncio
    async def test_close_with_items(self, pipeline_scheduler):
        """Test close with items in queue"""
        mock_pipeline = MagicMock()
        mock_pipeline.process_item = AsyncMock(return_value=True)
        mock_pipeline.process_error_item = AsyncMock()
        mock_pipeline.close = AsyncMock()
        pipeline_scheduler.item_pipelines.append(mock_pipeline)

        mock_item = MagicMock()
        mock_item.__retry_count__ = 0
        await pipeline_scheduler.item_queue.put(mock_item)

        result = await pipeline_scheduler.close()

        assert isinstance(result, PipelineProcessResult)
