"""同步管道调度器单元测试。

覆盖 SyncPipelineScheduler 的所有分支：
- open 默认/自定义/异步管道降级
- process 批量/时间触发
- _process_item 成功/失败
- error/retry item 处理
- close 排空队列
"""

import time

import pytest

from maize import SpiderSettings
from maize.common.items import Item
from maize.common.items.field import Field
from maize.sync.classic.pipeline.sync_base_pipeline import SyncBasePipeline
from maize.sync.classic.pipeline.sync_empty_pipeline import SyncEmptyPipeline
from maize.sync.classic.pipeline.sync_pipeline_scheduler import SyncPipelineScheduler
from maize.utils.log_util import set_spider_settings


class _TestItem(Item):
    url: str = Field()


class _SuccessPipeline(SyncBasePipeline):
    def __init__(self, settings):
        super().__init__(settings)
        self.processed: list = []
        self.closed = False

    def open(self):
        pass

    def close(self):
        self.closed = True

    def process_item(self, items: list) -> bool:
        self.processed.extend(items)
        return True

    def process_error_item(self, items: list):
        pass


class _FailPipeline(SyncBasePipeline):
    def __init__(self, settings):
        super().__init__(settings)
        self.error_items: list = []

    def open(self):
        pass

    def close(self):
        pass

    def process_item(self, items: list) -> bool:
        return False

    def process_error_item(self, items: list):
        self.error_items.extend(items)


@pytest.fixture(autouse=True)
def _setup():
    set_spider_settings(SpiderSettings())


class TestSyncPipelineSchedulerOpen:
    def test_default_empty_pipeline(self):
        settings = SpiderSettings()
        settings.pipeline.pipelines = []
        scheduler = SyncPipelineScheduler(settings)
        scheduler.open()
        assert len(scheduler.item_pipelines) == 1
        assert isinstance(scheduler.item_pipelines[0], SyncEmptyPipeline)

    def test_custom_pipeline_class(self):
        settings = SpiderSettings()
        settings.pipeline.pipelines = [_SuccessPipeline]
        scheduler = SyncPipelineScheduler(settings)
        scheduler.open()
        assert len(scheduler.item_pipelines) == 1
        assert isinstance(scheduler.item_pipelines[0], _SuccessPipeline)

    def test_async_pipeline_fallback(self):
        settings = SpiderSettings()
        # maize.EmptyPipeline is async — should fallback to SyncEmptyPipeline
        settings.pipeline.pipelines = ["maize.EmptyPipeline"]
        scheduler = SyncPipelineScheduler(settings)
        scheduler.open()
        assert len(scheduler.item_pipelines) == 1
        assert isinstance(scheduler.item_pipelines[0], SyncEmptyPipeline)

    def test_string_path_pipeline(self):
        settings = SpiderSettings()
        settings.pipeline.pipelines = ["maize.sync.classic.pipeline.sync_empty_pipeline.SyncEmptyPipeline"]
        scheduler = SyncPipelineScheduler(settings)
        scheduler.open()
        assert len(scheduler.item_pipelines) == 1


class TestSyncPipelineSchedulerProcess:
    def _make_scheduler(self, pipeline_cls=_SuccessPipeline, batch_size=10, interval=0):
        settings = SpiderSettings()
        settings.pipeline.pipelines = [pipeline_cls]
        settings.pipeline.handle_batch_max_size = batch_size
        settings.pipeline.handle_interval = interval
        scheduler = SyncPipelineScheduler(settings)
        scheduler.open()
        return scheduler

    def test_process_triggers_on_interval(self):
        scheduler = self._make_scheduler(interval=0)
        item = _TestItem(url="http://a.com")
        result = scheduler.process(item)
        assert result.success_count == 1

    def test_process_batch_full_triggers(self):
        settings = SpiderSettings()
        settings.pipeline.pipelines = [_SuccessPipeline]
        settings.pipeline.handle_batch_max_size = 2
        settings.pipeline.handle_interval = 9999
        settings.pipeline.max_cache_count = 2  # 队列满时触发处理
        scheduler = SyncPipelineScheduler(settings)
        scheduler.open()
        # 抑制时间触发，只测队列满触发
        scheduler._last_handle_item_time = int(time.time())
        scheduler.process(_TestItem(url="http://a.com"))
        result = scheduler.process(_TestItem(url="http://b.com"))
        assert result.success_count == 2

    def test_process_no_trigger_within_interval(self):
        scheduler = self._make_scheduler(batch_size=100, interval=9999)
        scheduler._last_handle_item_time = int(time.time())
        result = scheduler.process(_TestItem(url="http://a.com"))
        assert result.success_count == 0

    def test_process_failure_enqueues_retry(self):
        scheduler = self._make_scheduler(pipeline_cls=_FailPipeline, interval=0)
        item = _TestItem(url="http://a.com")
        result = scheduler.process(item)
        assert result.fail_count == 1
        assert scheduler.retry_item_queue.qsize() == 1

    def test_process_failure_exceeds_retry_goes_to_error(self):
        settings = SpiderSettings()
        settings.pipeline.pipelines = [_FailPipeline]
        settings.pipeline.handle_interval = 0
        settings.pipeline.error_max_retry_count = 1
        scheduler = SyncPipelineScheduler(settings)
        scheduler.open()

        item = _TestItem(url="http://a.com")
        item.__retry_count__ = 1  # already at max
        scheduler.process(item)
        assert scheduler.error_item_queue.qsize() == 1


class TestSyncPipelineSchedulerRetryAndError:
    def _make_scheduler(self, pipeline_cls=_FailPipeline):
        settings = SpiderSettings()
        settings.pipeline.pipelines = [pipeline_cls]
        settings.pipeline.handle_interval = 0
        settings.pipeline.error_handle_interval = 0
        settings.pipeline.error_max_retry_count = 2
        scheduler = SyncPipelineScheduler(settings)
        scheduler.open()
        return scheduler

    def test_retry_error_items_success(self):
        scheduler = self._make_scheduler(pipeline_cls=_SuccessPipeline)
        item = _TestItem(url="http://a.com")
        scheduler.retry_item_queue.put(item)
        # Need error_item_queue non-empty for process_retry_items to proceed
        scheduler.error_item_queue.put(_TestItem(url="http://err.com"))
        result = scheduler.process_retry_items()
        assert result.success_count == 1

    def test_retry_error_items_empty(self):
        scheduler = self._make_scheduler()
        result = scheduler.process_retry_items()
        assert result.success_count == 0

    def test_process_error_items(self):
        scheduler = self._make_scheduler()
        scheduler.error_item_queue.put(_TestItem(url="http://a.com"))
        scheduler.process_error_items()
        assert scheduler.error_item_queue.qsize() == 0

    def test_single_process_error_items_empty(self):
        scheduler = self._make_scheduler()
        scheduler._single_process_error_items()  # no-op

    def test_close_drains_queues(self):
        scheduler = self._make_scheduler(pipeline_cls=_SuccessPipeline)
        scheduler.item_queue.put(_TestItem(url="http://a.com"))
        scheduler.item_queue.put(_TestItem(url="http://b.com"))
        result = scheduler.close()
        assert result.success_count == 2
        assert scheduler.item_pipelines[0].closed

    def test_close_with_retry_items(self):
        scheduler = self._make_scheduler(pipeline_cls=_SuccessPipeline)
        item = _TestItem(url="http://a.com")
        scheduler.retry_item_queue.put(item)
        scheduler.error_item_queue.put(_TestItem(url="http://err.com"))
        result = scheduler.close()
        assert result.success_count >= 1

    def test_idle_and_error_task_idle(self):
        scheduler = self._make_scheduler()
        assert scheduler.idle() is True
        assert scheduler.error_task_idle() is True
        scheduler.item_queue.put(_TestItem(url="http://a.com"))
        assert scheduler.idle() is False
        scheduler.error_item_queue.put(_TestItem(url="http://b.com"))
        assert scheduler.error_task_idle() is False
