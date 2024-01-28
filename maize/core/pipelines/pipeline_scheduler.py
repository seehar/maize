import time
from asyncio import Queue
from typing import TYPE_CHECKING

from maize.utils.log_util import get_logger
from maize.utils.project_util import load_class


if TYPE_CHECKING:
    from maize import BasePipeline
    from maize import Item
    from maize.core.settings.settings_manager import SettingsManager


class PipelineScheduler:
    """
    管道数据调度
    """

    def __init__(self, settings: "SettingsManager"):
        self.settings = settings
        self.logger = get_logger(settings, self.__class__.__name__)
        self.item_pipelines: list["BasePipeline"] = []

        # item
        item_max_cache_count = settings.getint("ITEM_MAX_CACHE_COUNT")
        self.item_handle_batch_max_size = settings.getint("ITEM_HANDLE_BATCH_MAX_SIZE")
        self.item_handle_interval = settings.getint("ITEM_HANDLE_INTERVAL")

        self.item_queue = Queue(maxsize=item_max_cache_count)
        self._last_handle_item_time = 0

        # error item
        self.error_item_max_retry_count = settings.getint("ERROR_ITEM_MAX_RETRY_COUNT")
        error_item_max_cache_count = settings.getint("ERROR_ITEM_MAX_CACHE_COUNT")
        self.error_item_retry_batch_max_size = settings.getint(
            "ERROR_ITEM_RETRY_BATCH_MAX_SIZE"
        )
        self.error_item_handle_batch_max_size = settings.getint(
            "ERROR_ITEM_HANDLE_BATCH_MAX_SIZE"
        )
        self.error_item_handle_interval = settings.getint("ERROR_ITEM_HANDLE_INTERVAL")
        self.error_item_queue = Queue(maxsize=error_item_max_cache_count)
        self._error_last_handle_item_time = 0

        # retry item
        self.retry_item_queue = Queue(maxsize=error_item_max_cache_count)

    async def open(self):
        pipeline_path_list = self.settings.getlist("ITEM_PIPELINES")
        for pipeline_path in pipeline_path_list:
            self.logger.info(f"Loading pipeline: {pipeline_path}")
            pipeline_instance = load_class(pipeline_path)(self.settings)
            await pipeline_instance.open()
            self.item_pipelines.append(pipeline_instance)

    async def close(self):
        self.logger.debug("pipeline scheduler closing")
        while not self.item_queue.empty():
            await self._process_item()
            # 重试
            await self._retry_error_items()

        self.logger.debug("process all items finished")
        # 重试错误 item
        while not self.retry_item_queue.empty():
            retry_result = await self._retry_error_items()
            if not retry_result:
                self.logger.info(f"任务重试完成，剩余错误任务: {self.retry_item_queue.qsize()}")
                break

        # 处理错误 item
        await self.process_error_items()

        self.logger.debug("process retry all items finished")

        for pipeline in self.item_pipelines:
            await pipeline.close()
        self.logger.debug("pipeline scheduler closed")

    async def process(self, item: "Item"):
        await self.item_queue.put(item)
        current_time = int(time.time())
        if (
            (current_time - self.item_handle_interval) > self._last_handle_item_time
        ) or self.item_queue.full():
            self._last_handle_item_time = current_time
            await self._process_item()
            await self.process_retry_items()

    async def _process_item(self):
        """
        处理 item
        @return:
        """
        batch_items = []
        for _ in range(self.item_handle_batch_max_size):
            if self.item_queue.empty():
                break

            batch_items.append(await self.item_queue.get())

        if not batch_items:
            self.logger.debug("no more items to process")
            return

        for pipeline in self.item_pipelines:
            process_item_result = await pipeline.process_item(batch_items)
            if not process_item_result:
                await self._enqueue_retry_items(batch_items)

    async def process_error_items(self):
        self.logger.info(f"需要处理的错误任务个数: {self.error_item_queue.qsize()}")
        while not self.error_item_queue.empty():
            await self._single_process_error_items()

    async def _single_process_error_items(self):
        """
        处理超过指定重试次数的 item
        @return:
        """
        if self.error_item_queue.empty():
            return

        batch_items = []
        for _ in range(self.error_item_handle_batch_max_size):
            if self.error_item_queue.empty():
                break

            error_item: "Item" = await self.error_item_queue.get()
            batch_items.append(error_item)

        if not batch_items:
            self.logger.debug("no more error items to process")
            return

        for pipeline in self.item_pipelines:
            await pipeline.process_error_item(batch_items)

    async def process_retry_items(self):
        """
        处理错误的 item
        重试指定次数，超过重试次数后，调用 pipeline 的 方法
        @return:
        """
        if self.error_item_queue.empty():
            return

        current_time = int(time.time())
        if (
            current_time - self.error_item_handle_interval
        ) > self._error_last_handle_item_time or self.error_item_queue.full():
            self._error_last_handle_item_time = current_time
            await self._retry_error_items()

    async def _retry_error_items(self) -> bool:
        """
        处理错误的 item，全部重试完成后停止
        @return: True 存在未完成的任务，False 不存在任务
        """
        self.logger.info("retry error items")
        batch_items = []
        for _ in range(self.error_item_retry_batch_max_size):
            if self.retry_item_queue.empty():
                break

            error_item: "Item" = await self.retry_item_queue.get()
            error_item.retry()
            batch_items.append(error_item)

        if not batch_items:
            self.logger.debug("no more error items to retry")
            return False

        for pipeline in self.item_pipelines:
            # 调用正常处理方法重试
            process_item_result = await pipeline.process_item(batch_items)
            if not process_item_result:
                await self._enqueue_retry_items(batch_items)
        return True

    async def _enqueue_retry_items(self, items: list["Item"]) -> None:
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

    def __len__(self):
        return self.item_queue.qsize()

    def error_task_idle(self):
        return self.error_item_queue.qsize() == 0
