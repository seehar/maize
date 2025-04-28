import asyncio
import datetime
from contextlib import asynccontextmanager
from typing import Any
from typing import AsyncGenerator
from typing import Optional

from maize.common.model.statistics_model import SpiderStatistics
from maize.settings import SpiderSettings
from maize.utils.log_util import get_logger


class StatsCollector:
    def __init__(self, settings: SpiderSettings):
        self._lock = asyncio.Lock()
        self._stats: dict[str, SpiderStatistics] = {}
        self._start_time: Optional[datetime.datetime] = None
        self._end_time: Optional[datetime.datetime] = None

        self._logger = get_logger(settings, self.__class__.__name__)

    async def open(self):
        self._start_time = datetime.datetime.now()

    async def close(self):
        self._end_time = datetime.datetime.now()

        self._logger.info("-" * 100)
        self._logger.info(f"爬虫运行时间: {self._start_time} ~ {self._end_time}")
        self._logger.info(f"耗时: {(self._end_time - self._start_time).total_seconds()}s")
        await self.show_all()
        self._logger.info("-" * 100)

    @staticmethod
    def _get_minute_key(dt: Optional[datetime.datetime] = None) -> str:
        dt = dt or datetime.datetime.now()
        return dt.strftime("%Y-%m-%d %H:%M")

    @asynccontextmanager
    async def _increment(self) -> AsyncGenerator[SpiderStatistics, Any]:
        minute_key = self._get_minute_key()
        async with self._lock:
            if minute_key not in self._stats:
                self._stats[minute_key] = SpiderStatistics()

            yield self._stats[minute_key]

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

    async def show_all(self):
        async with self._lock:
            for key, value in self._stats.items():
                self._logger.info(f"{key}: {value.get_dict()}")
