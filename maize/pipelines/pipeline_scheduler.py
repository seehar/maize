import time
from asyncio import Queue
from typing import TYPE_CHECKING

from maize.common.model.pipeline_model import PipelineProcessResult
from maize.utils.log_util import get_logger
from maize.utils.project_util import load_class

if TYPE_CHECKING:
    from maize import BasePipeline, Item
    from maize.settings import SpiderSettings


class PipelineScheduler:
    """
    管道数据调度
    """

    def __init__(self, settings: "SpiderSettings"):
        self.settings = settings
        self.logger = get_logger(settings, self.__class__.__name__)
        self.item_pipelines: list[BasePipeline] = []

        # item
        pipeline_settings = settings.pipeline
        item_max_cache_count = pipeline_settings.max_cache_count
        self.item_handle_batch_max_size = pipeline_settings.handle_batch_max_size
        self.item_handle_interval = pipeline_settings.handle_interval

        self.item_queue = Queue(maxsize=item_max_cache_count)
        self._last_handle_item_time = 0

        # error item
        self.error_item_max_retry_count = pipeline_settings.error_max_retry_count
        error_item_max_cache_count = pipeline_settings.error_max_cache_count
        self.error_item_retry_batch_max_size = pipeline_settings.error_retry_batch_max_size
        self.error_item_handle_batch_max_size = pipeline_settings.error_handle_batch_max_size
        self.error_item_handle_interval = pipeline_settings.error_handle_interval
        self.error_item_queue = Queue(maxsize=error_item_max_cache_count)
        self._error_last_handle_item_time = 0

        # retry item
        self.retry_item_queue = Queue(maxsize=error_item_max_cache_count)

    def __len__(self):
        return self.item_queue.qsize()

    async def open(self):
        pipeline_path_list = self.settings.pipeline.pipelines
        for pipeline_path in pipeline_path_list:
            self.logger.info(f"Loading pipeline: {pipeline_path}")
            pipeline_instance = load_class(pipeline_path)(self.settings)
            await pipeline_instance.open()
            self.item_pipelines.append(pipeline_instance)

    async def close(self) -> PipelineProcessResult:
        self.logger.debug("pipeline scheduler closing")
        close_process_result = PipelineProcessResult()
        while not self.item_queue.empty():
            process_item = await self._process_item()
            close_process_result.add(process_item)

            # 重试
            _, retry_process_result = await self._retry_error_items()
            close_process_result.add(retry_process_result)

        self.logger.debug("process all items finished")
        # 重试错误 item
        while not self.retry_item_queue.empty():
            retry_result, retry_error_process_result = await self._retry_error_items()
            close_process_result.add(retry_error_process_result)
            if not retry_result:
                self.logger.info(f"任务重试完成，剩余错误任务: {self.retry_item_queue.qsize()}")
                break

        # 处理超过重试次数的 item
        await self.process_error_items()

        self.logger.debug("process retry all items finished")

        for pipeline in self.item_pipelines:
            await pipeline.close()
        self.logger.debug("pipeline scheduler closed")
        return close_process_result

    async def process(self, item: "Item") -> PipelineProcessResult:
        pipeline_process_result = PipelineProcessResult()
        await self.item_queue.put(item)
        current_time = int(time.time())
        if ((current_time - self.item_handle_interval) > self._last_handle_item_time) or self.item_queue.full():
            self._last_handle_item_time = current_time
            process_result = await self._process_item()
            retry_process_result = await self.process_retry_items()
            pipeline_process_result.add(process_result)
            pipeline_process_result.add(retry_process_result)
        return pipeline_process_result

    async def _process_item(self) -> PipelineProcessResult:
        """
        处理 item

        :return: 处理结果
        """
        process_result = PipelineProcessResult()
        batch_items = []
        for _ in range(self.item_handle_batch_max_size):
            if self.item_queue.empty():
                break

            batch_items.append(await self.item_queue.get())

        if not batch_items:
            self.logger.debug("no more items to process")
            return process_result

        batch_items_len = len(batch_items)
        for pipeline in self.item_pipelines:
            process_item_result = await pipeline.process_item(batch_items)
            if not process_item_result:
                process_result.fail_count += batch_items_len
                await self._enqueue_retry_items(batch_items)
            else:
                process_result.success_count += batch_items_len
        return process_result

    async def process_error_items(self):
        self.logger.info(f"需要处理的错误任务个数: {self.error_item_queue.qsize()}")
        while not self.error_item_queue.empty():
            await self._single_process_error_items()

    async def _single_process_error_items(self):
        """
        处理超过指定重试次数的 item

        :return:
        """
        if self.error_item_queue.empty():
            return

        batch_items = []
        for _ in range(self.error_item_handle_batch_max_size):
            if self.error_item_queue.empty():
                break

            error_item: Item = await self.error_item_queue.get()
            batch_items.append(error_item)

        if not batch_items:
            self.logger.debug("no more error items to process")
            return

        for pipeline in self.item_pipelines:
            await pipeline.process_error_item(batch_items)

    async def process_retry_items(self) -> PipelineProcessResult:
        """
        处理错误的 item
        重试指定次数，超过重试次数后，调用 pipeline 的 方法

        :return:
        """
        process_result = PipelineProcessResult()
        if self.error_item_queue.empty():
            return process_result

        current_time = int(time.time())
        if (
            current_time - self.error_item_handle_interval
        ) > self._error_last_handle_item_time or self.error_item_queue.full():
            self._error_last_handle_item_time = current_time
            _, retry_result = await self._retry_error_items()
            process_result.add(retry_result)
        return process_result

    async def _retry_error_items(self) -> tuple[bool, PipelineProcessResult]:
        """
        处理错误的 item，全部重试完成后停止

        :return: True 存在未完成的任务，False 不存在任务
        """
        process_result = PipelineProcessResult()
        self.logger.info("retry error items")
        batch_items = []
        for _ in range(self.error_item_retry_batch_max_size):
            if self.retry_item_queue.empty():
                break

            error_item: Item = await self.retry_item_queue.get()
            error_item.retry()
            batch_items.append(error_item)

        if not batch_items:
            self.logger.debug("no more error items to retry")
            return False, process_result

        for pipeline in self.item_pipelines:
            # 调用正常处理方法重试
            process_item_result = await pipeline.process_item(batch_items)
            if not process_item_result:
                process_result.fail_count += len(batch_items)
                await self._enqueue_retry_items(batch_items)
            else:
                process_result.success_count += len(batch_items)
        return True, process_result

    async def _enqueue_retry_items(self, items: list["Item"]):
        """
        入队需要重试的 item

        :param items:
        :return:
        """
        for item in items:
            if item.__retry_count__ >= self.error_item_max_retry_count:
                self.logger.warning(
                    f"超过重试次数({item.__retry_count__}/{self.error_item_max_retry_count}) item: {item}"
                )
                await self.error_item_queue.put(item)
            else:
                await self.retry_item_queue.put(item)

    def idle(self):
        return len(self) == 0

    def error_task_idle(self):
        return self.error_item_queue.qsize() == 0
