"""同步管道调度器。

与异步版 ``PipelineScheduler`` 对应，使用 ``queue.Queue`` 替代 ``asyncio.Queue``。
批量处理、错误重试、超限处理逻辑与异步版一致。
"""

import queue
import time
from typing import TYPE_CHECKING

from maize.common.model.pipeline_model import PipelineProcessResult
from maize.sync.classic.pipeline.sync_empty_pipeline import SyncEmptyPipeline
from maize.utils.log_util import get_logger
from maize.utils.project_util import load_class

if TYPE_CHECKING:
    from maize.common.items import Item
    from maize.settings import SpiderSettings
    from maize.sync.classic.pipeline.sync_base_pipeline import SyncBasePipeline


class SyncPipelineScheduler:
    """同步管道数据调度。"""

    def __init__(self, settings: "SpiderSettings"):
        self.settings = settings
        self.logger = get_logger(settings, self.__class__.__name__)
        self.item_pipelines: list[SyncBasePipeline] = []

        # item
        pipeline_settings = settings.pipeline
        item_max_cache_count = pipeline_settings.max_cache_count
        self.item_handle_batch_max_size = pipeline_settings.handle_batch_max_size
        self.item_handle_interval = pipeline_settings.handle_interval

        self.item_queue: queue.Queue = queue.Queue(maxsize=item_max_cache_count)
        self._last_handle_item_time = 0

        # error item
        self.error_item_max_retry_count = pipeline_settings.error_max_retry_count
        error_item_max_cache_count = pipeline_settings.error_max_cache_count
        self.error_item_retry_batch_max_size = pipeline_settings.error_retry_batch_max_size
        self.error_item_handle_batch_max_size = pipeline_settings.error_handle_batch_max_size
        self.error_item_handle_interval = pipeline_settings.error_handle_interval
        self.error_item_queue: queue.Queue = queue.Queue(maxsize=error_item_max_cache_count)
        self._error_last_handle_item_time = 0

        # retry item
        self.retry_item_queue: queue.Queue = queue.Queue()

    def __len__(self):
        return self.item_queue.qsize()

    def open(self):
        pipeline_path_list = self.settings.pipeline.pipelines
        if not pipeline_path_list:
            # 默认使用同步空管道
            pipeline_instance = SyncEmptyPipeline(self.settings)
            pipeline_instance.open()
            self.item_pipelines.append(pipeline_instance)
            return

        for pipeline_path in pipeline_path_list:
            self.logger.info(f"Loading pipeline: {pipeline_path}")
            if isinstance(pipeline_path, str):
                pipeline_instance = load_class(pipeline_path)(self.settings)
            else:
                pipeline_instance = pipeline_path(self.settings)
            pipeline_instance.open()
            self.item_pipelines.append(pipeline_instance)

    def close(self) -> PipelineProcessResult:
        self.logger.debug("pipeline scheduler closing")
        close_process_result = PipelineProcessResult()
        while not self.item_queue.empty():
            process_item = self._process_item()
            close_process_result.add(process_item)

            _, retry_process_result = self._retry_error_items()
            close_process_result.add(retry_process_result)

        self.logger.debug("process all items finished")
        while not self.retry_item_queue.empty():
            retry_result, retry_error_process_result = self._retry_error_items()
            close_process_result.add(retry_error_process_result)
            if not retry_result:
                self.logger.info(f"任务重试完成，剩余错误任务: {self.retry_item_queue.qsize()}")
                break

        self.process_error_items()

        self.logger.debug("process retry all items finished")

        for pipeline in self.item_pipelines:
            pipeline.close()
        self.logger.debug("pipeline scheduler closed")
        return close_process_result

    def process(self, item: "Item") -> PipelineProcessResult:
        pipeline_process_result = PipelineProcessResult()
        self.item_queue.put(item)
        current_time = int(time.time())
        if ((current_time - self.item_handle_interval) > self._last_handle_item_time) or (
            self.item_queue.full() if self.item_queue.maxsize > 0 else False
        ):
            self._last_handle_item_time = current_time
            process_result = self._process_item()
            retry_process_result = self.process_retry_items()
            pipeline_process_result.add(process_result)
            pipeline_process_result.add(retry_process_result)
        return pipeline_process_result

    def _process_item(self) -> PipelineProcessResult:
        process_result = PipelineProcessResult()
        batch_items = []
        for _ in range(self.item_handle_batch_max_size):
            if self.item_queue.empty():
                break
            batch_items.append(self.item_queue.get())

        if not batch_items:
            self.logger.debug("no more items to process")
            return process_result

        batch_items_len = len(batch_items)
        for pipeline in self.item_pipelines:
            process_item_result = pipeline.process_item(batch_items)
            if not process_item_result:
                process_result.fail_count += batch_items_len
                self._enqueue_retry_items(batch_items)
            else:
                process_result.success_count += batch_items_len
        return process_result

    def process_error_items(self):
        self.logger.info(f"需要处理的错误任务个数: {self.error_item_queue.qsize()}")
        while not self.error_item_queue.empty():
            self._single_process_error_items()

    def _single_process_error_items(self):
        if self.error_item_queue.empty():
            return

        batch_items = []
        for _ in range(self.error_item_handle_batch_max_size):
            if self.error_item_queue.empty():
                break
            error_item = self.error_item_queue.get()
            batch_items.append(error_item)

        if not batch_items:
            self.logger.debug("no more error items to process")
            return

        for pipeline in self.item_pipelines:
            pipeline.process_error_item(batch_items)

    def process_retry_items(self) -> PipelineProcessResult:
        process_result = PipelineProcessResult()
        if self.error_item_queue.empty():
            return process_result

        current_time = int(time.time())
        if (current_time - self.error_item_handle_interval) > self._error_last_handle_item_time or (
            self.error_item_queue.full() if self.error_item_queue.maxsize > 0 else False
        ):
            self._error_last_handle_item_time = current_time
            _, retry_result = self._retry_error_items()
            process_result.add(retry_result)
        return process_result

    def _retry_error_items(self) -> tuple[bool, PipelineProcessResult]:
        process_result = PipelineProcessResult()
        self.logger.info("retry error items")
        batch_items = []
        for _ in range(self.error_item_retry_batch_max_size):
            if self.retry_item_queue.empty():
                break
            error_item = self.retry_item_queue.get()
            error_item.retry()
            batch_items.append(error_item)

        if not batch_items:
            self.logger.debug("no more error items to retry")
            return False, process_result

        for pipeline in self.item_pipelines:
            process_item_result = pipeline.process_item(batch_items)
            if not process_item_result:
                process_result.fail_count += len(batch_items)
                self._enqueue_retry_items(batch_items)
            else:
                process_result.success_count += len(batch_items)
        return True, process_result

    def _enqueue_retry_items(self, items: list["Item"]):
        for item in items:
            if item.__retry_count__ >= self.error_item_max_retry_count:
                self.logger.warning(
                    f"超过重试次数({item.__retry_count__}/{self.error_item_max_retry_count}) item: {item}"
                )
                self.error_item_queue.put(item)
            else:
                self.retry_item_queue.put(item)

    def idle(self):
        return len(self) == 0

    def error_task_idle(self):
        return self.error_item_queue.qsize() == 0
