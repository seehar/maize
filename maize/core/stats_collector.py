import asyncio
import datetime
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import httpx

from maize.common.model.statistics_model import SpiderStatistics
from maize.common.model.upload_model import MaizeUploadModel
from maize.core.task_manager import TaskManager
from maize.settings import SpiderSettings
from maize.utils.log_util import get_logger
from maize.utils.system_util import get_container_id


class StatsCollector:
    def __init__(self, settings: SpiderSettings, spider_name: str):
        self._settings = settings
        self._spider_name = spider_name

        self._lock = asyncio.Lock()
        self._stats: dict[str, SpiderStatistics] = {}
        self._start_time: datetime.datetime | None = None
        self._end_time: datetime.datetime | None = None

        self._logger = get_logger(settings, self.__class__.__name__)

        self._task_manager = TaskManager()
        self._last_upload_key: str = ""
        self._container_id: str = ""

    async def open(self):
        if container_id := get_container_id():
            self._container_id = container_id

        self._start_time = datetime.datetime.now()

    async def close(self):
        self._end_time = datetime.datetime.now()

        if self._stats:
            key_list = list(self._stats.keys())
            for key in key_list:
                await self._upload_stat(key)

        self._logger.info("-" * 100)
        self._logger.info(f"爬虫运行时间: {self._start_time} ~ {self._end_time}")
        self._logger.info(f"耗时: {(self._end_time - self._start_time).total_seconds()}s")
        self._logger.info("-" * 100)

    @staticmethod
    def _get_minute_key() -> tuple[str, str]:
        now = datetime.datetime.now()
        pre_minute = now - datetime.timedelta(minutes=1)
        return now.strftime("%Y-%m-%d %H:%M"), pre_minute.strftime("%Y-%m-%d %H:%M")

    @asynccontextmanager
    async def _increment(self) -> AsyncGenerator[SpiderStatistics, Any]:
        minute_key, pre_minute_key = self._get_minute_key()
        async with self._lock:
            if minute_key not in self._stats:
                self._stats[minute_key] = SpiderStatistics()

            yield self._stats[minute_key]
            await self._upload_stat(pre_minute_key)

    async def record_download_success(self, status_code: int):
        status_code_str = str(status_code)
        async with self._increment() as stats:
            stats.download_success_count += 1
            stats.download_total += 1

            if status_code_str not in stats.download_status:
                stats.download_status[status_code_str] = 0
            stats.download_status[status_code_str] += 1

    async def record_download_fail(self, reason: str):
        """
        记录下载失败的数据

        :param reason: 失败原因
        :return:
        """
        async with self._increment() as stats:
            stats.download_fail_count += 1
            stats.download_total += 1

            if reason not in stats.download_fail_reason:
                stats.download_fail_reason[reason] = 0
            stats.download_fail_reason[reason] += 1

    async def record_parse_success(self):
        async with self._increment() as stats:
            stats.parse_success_count += 1

    async def record_parse_fail(self):
        async with self._increment() as stats:
            stats.parse_fail_count += 1

    async def record_pipeline_success(self, count: int = 1):
        if not count:
            return

        async with self._increment() as stats:
            stats.pipeline_success_count += count

    async def record_pipeline_fail(self, count: int = 1):
        if not count:
            return

        async with self._increment() as stats:
            stats.pipeline_fail_count += count

    async def get_and_clear_stats(self, minute_key: str):
        async with self._lock:
            stats = self._stats.get(minute_key, None)
            if stats:
                del self._stats[minute_key]
            return stats

    async def _upload_stat(self, pre_minute_key: str):
        if self._last_upload_key == pre_minute_key or pre_minute_key not in self._stats:
            return

        if not self._last_upload_key and len(self._stats) == 1:
            return

        pre_minute_stat = self._stats[pre_minute_key]
        maize_upload_model = MaizeUploadModel()
        maize_upload_model.pid = os.getpid()
        maize_upload_model.stat_time = pre_minute_key
        maize_upload_model.spider_name = self._spider_name
        maize_upload_model.project_name = self._settings.project_name
        maize_upload_model.container_id = self._container_id

        maize_upload_model_dict = maize_upload_model.model_dump()
        maize_upload_model_dict.update(pre_minute_stat.model_dump())
        self._logger.info(f"stat: {maize_upload_model_dict}")

        if not self._settings.maize_cob_api:
            del self._stats[pre_minute_key]
            self._last_upload_key = pre_minute_key
            return

        async def upload_stat() -> None:
            for _ in range(3):
                try:
                    async with httpx.AsyncClient() as client:
                        response = await client.post(self._settings.maize_cob_api, json=maize_upload_model_dict)
                        self._logger.info(f"upload stat: <{response.status_code}> {response.text}")
                    del self._stats[pre_minute_key]
                    self._last_upload_key = pre_minute_key
                    break
                except Exception as e:
                    self._logger.warning(f"upload stat error: {e}，准备第 {_ + 1} 次重试")

        await self._task_manager.semaphore.acquire()
        self._task_manager.create_task(upload_stat())

    def idle(self) -> bool:
        return self._task_manager.all_done()
