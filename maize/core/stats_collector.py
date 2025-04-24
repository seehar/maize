import asyncio
import datetime
from contextlib import asynccontextmanager
from typing import Any
from typing import AsyncGenerator
from typing import Optional

from maize.common.model.statistics_model import SpiderStatistics


class StatsCollector:
    def __init__(self):
        self._lock = asyncio.Lock()
        self._stats: dict[str, SpiderStatistics] = {}
        self._start_time: Optional[datetime.datetime] = None
        self._end_time: Optional[datetime.datetime] = None

    async def open(self):
        self._start_time = datetime.datetime.now()

    async def close(self):
        self._end_time = datetime.datetime.now()

        print("-" * 100)
        print(f"爬虫运行时间: {self._start_time} ~ {self._end_time}")
        print(f"耗时: {(self._end_time - self._start_time).total_seconds()}s")
        await self.show_all()
        print("-" * 100)

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

    async def record_download_success(self):
        async with self._increment() as stats:
            stats.download_success_count += 1
            stats.download_total += 1

    async def record_download_fail(self):
        async with self._increment() as stats:
            stats.download_fail_count += 1
            stats.download_total += 1

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
                print(f"{key}: {value.get_dict()}")
