"""
Tests for PipelineScheduler close/retry/error full paths.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from maize.common.items import Item
from maize.pipelines.pipeline_scheduler import PipelineScheduler
from maize.settings import SpiderSettings


class TestItem(Item):
    __table_name__: str = "test"
    name: str = ""


def _make_scheduler():
    settings = SpiderSettings()
    settings.pipeline.handle_interval = 0
    settings.pipeline.error_handle_interval = 0
    return PipelineScheduler(settings)


class TestPipelineSchedulerClose:
    """Cover close() with pending items + retry loop + error items."""

    @pytest.mark.asyncio
    async def test_close_with_retry_items(self):
        """close() processes retry_item_queue items."""
        scheduler = _make_scheduler()
        mock_pipeline = MagicMock()
        mock_pipeline.process_item = AsyncMock(return_value=True)
        mock_pipeline.process_error_item = AsyncMock()
        mock_pipeline.close = AsyncMock()
        scheduler.item_pipelines.append(mock_pipeline)

        # Put item in retry queue
        item = TestItem(name="retry-me")
        await scheduler.retry_item_queue.put(item)

        await scheduler.close()
        # Item was retried successfully
        mock_pipeline.process_item.assert_called()
        mock_pipeline.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_with_failed_retry(self):
        """close() with retry failure moves item to error queue."""
        scheduler = _make_scheduler()
        mock_pipeline = MagicMock()
        mock_pipeline.process_item = AsyncMock(return_value=False)
        mock_pipeline.process_error_item = AsyncMock()
        mock_pipeline.close = AsyncMock()
        scheduler.item_pipelines.append(mock_pipeline)

        # Put item in retry queue with retry count at max
        item = TestItem(name="fail")
        for _ in range(scheduler.error_item_max_retry_count + 1):
            item.retry()
        await scheduler.retry_item_queue.put(item)

        await scheduler.close()
        # Item goes to error queue, process_error_item called
        mock_pipeline.process_error_item.assert_called()

    @pytest.mark.asyncio
    async def test_close_empty_all_queues(self):
        """close() with empty queues just closes pipelines."""
        scheduler = _make_scheduler()
        mock_pipeline = MagicMock()
        mock_pipeline.close = AsyncMock()
        scheduler.item_pipelines.append(mock_pipeline)

        await scheduler.close()
        mock_pipeline.close.assert_called_once()


class TestPipelineSchedulerProcessRetryItems:
    """Cover process_retry_items path."""

    @pytest.mark.asyncio
    async def test_process_retry_items_empty_error_queue(self):
        scheduler = _make_scheduler()
        result = await scheduler.process_retry_items()
        assert result.success_count == 0
        assert result.fail_count == 0

    @pytest.mark.asyncio
    async def test_process_retry_items_with_items(self):
        scheduler = _make_scheduler()
        mock_pipeline = MagicMock()
        mock_pipeline.process_item = AsyncMock(return_value=True)
        scheduler.item_pipelines.append(mock_pipeline)

        # Put item in retry queue (process_retry_items checks error_item_queue first)
        item = TestItem(name="retry")
        await scheduler.retry_item_queue.put(item)
        await scheduler.error_item_queue.put(item)  # trigger the error queue path
        scheduler._error_last_handle_item_time = 0

        result = await scheduler.process_retry_items()
        assert result.success_count == 1


class TestPipelineSchedulerEnqueueRetry:
    """Cover _enqueue_retry_items path."""

    @pytest.mark.asyncio
    async def test_enqueue_retry_under_max(self):
        scheduler = _make_scheduler()
        item = TestItem(name="retry")
        await scheduler._enqueue_retry_items([item])
        assert not scheduler.retry_item_queue.empty()
        assert scheduler.error_item_queue.empty()

    @pytest.mark.asyncio
    async def test_enqueue_retry_over_max_goes_to_error(self):
        scheduler = _make_scheduler()
        item = TestItem(name="exhausted")
        for _ in range(scheduler.error_item_max_retry_count + 1):
            item.retry()
        await scheduler._enqueue_retry_items([item])
        assert scheduler.error_item_queue.empty() is False
        assert scheduler.retry_item_queue.empty()


class TestPipelineSchedulerProcessErrorItems:
    """Cover process_error_items and _single_process_error_items."""

    @pytest.mark.asyncio
    async def test_process_error_items_empty(self):
        scheduler = _make_scheduler()
        await scheduler.process_error_items()

    @pytest.mark.asyncio
    async def test_process_error_items_with_items(self):
        scheduler = _make_scheduler()
        mock_pipeline = MagicMock()
        mock_pipeline.process_error_item = AsyncMock()
        scheduler.item_pipelines.append(mock_pipeline)

        item = TestItem(name="error")
        await scheduler.error_item_queue.put(item)

        await scheduler.process_error_items()
        mock_pipeline.process_error_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_single_process_error_items_empty(self):
        scheduler = _make_scheduler()
        await scheduler._single_process_error_items()

    @pytest.mark.asyncio
    async def test_single_process_error_items_batch(self):
        scheduler = _make_scheduler()
        mock_pipeline = MagicMock()
        mock_pipeline.process_error_item = AsyncMock()
        scheduler.item_pipelines.append(mock_pipeline)

        for i in range(3):
            await scheduler.error_item_queue.put(TestItem(name=f"err{i}"))

        await scheduler._single_process_error_items()
        mock_pipeline.process_error_item.assert_called_once()


class TestPipelineSchedulerRetryErrorItems:
    """Cover _retry_error_items path."""

    @pytest.mark.asyncio
    async def test_retry_empty_returns_false(self):
        scheduler = _make_scheduler()
        result, _process_result = await scheduler._retry_error_items()
        assert result is False

    @pytest.mark.asyncio
    async def test_retry_success(self):
        scheduler = _make_scheduler()
        mock_pipeline = MagicMock()
        mock_pipeline.process_item = AsyncMock(return_value=True)
        scheduler.item_pipelines.append(mock_pipeline)

        item = TestItem(name="retry")
        await scheduler.retry_item_queue.put(item)

        result, process_result = await scheduler._retry_error_items()
        assert result is True
        assert process_result.success_count == 1

    @pytest.mark.asyncio
    async def test_retry_failure_re_enqueues(self):
        scheduler = _make_scheduler()
        mock_pipeline = MagicMock()
        mock_pipeline.process_item = AsyncMock(return_value=False)
        scheduler.item_pipelines.append(mock_pipeline)

        item = TestItem(name="fail")
        await scheduler.retry_item_queue.put(item)

        result, process_result = await scheduler._retry_error_items()
        assert result is True
        assert process_result.fail_count == 1
