import asyncio
import datetime
import os
from contextlib import asynccontextmanager
from dataclasses import asdict
from typing import Any
from typing import AsyncGenerator
from typing import Optional

import httpx

from maize.common.model.statistics_model import SpiderStatistics
from maize.common.model.upload_model import MaizeUploadModel
from maize.core.task_manager import TaskManager
from maize.settings import SpiderSettings
from maize.utils.log_util import get_logger


class StatsCollector:
    def __init__(self, settings: SpiderSettings, spider_name: str):
        self._settings = settings
        self._spider_name = spider_name

        self._lock = asyncio.Lock()
        self._stats: dict[str, SpiderStatistics] = {}
        self._start_time: Optional[datetime.datetime] = None
        self._end_time: Optional[datetime.datetime] = None

        self._logger = get_logger(settings, self.__class__.__name__)

        self._task_manager = TaskManager()
        self._last_upload_key: str = ""

    async def open(self):
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
        async with self._increment() as stats:
            stats.download_success_count += 1
            stats.download_total += 1

            if status_code not in stats.download_status:
                stats.download_status[status_code] = 0
            stats.download_status[status_code] += 1

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
        maize_upload_model.now = pre_minute_key
        maize_upload_model.spider_name = self._spider_name
        maize_upload_model.project_name = self._settings.PROJECT_NAME
        maize_upload_model.stat = pre_minute_stat

        if not self._settings.MAIZE_COB_API:
            self._logger.info(f"stat: {asdict(maize_upload_model)}")
            del self._stats[pre_minute_key]
            self._last_upload_key = pre_minute_key
            return

        async def upload_stat() -> None:
            async with httpx.AsyncClient() as client:
                await client.post(self._settings.MAIZE_COB_API, json=asdict(maize_upload_model))
            del self._stats[pre_minute_key]
            self._last_upload_key = pre_minute_key

        await self._task_manager.semaphore.acquire()
        self._task_manager.create_task(upload_stat())

    def idle(self) -> bool:
        return self._task_manager.all_done()
