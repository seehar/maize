"""同步统计收集器。

与异步版 ``StatsCollector`` 对应，所有方法为同步（非 async）。
使用 ``threading.Lock`` 替代 ``asyncio.Lock``，使用同步 ``httpx.Client`` 上传统计。
线程安全，可在 SyncEngine 的线程池中安全调用。
"""

import datetime
import os
import threading

import httpx

from maize.common.model.statistics_model import SpiderStatistics
from maize.common.model.upload_model import MaizeUploadModel
from maize.utils.log_util import get_logger, get_spider_settings
from maize.utils.system_util import get_container_id


class SyncStatsCollector:
    """同步统计收集器，线程安全。"""

    def __init__(self, spider_name: str):
        self._settings = get_spider_settings()
        self._spider_name = spider_name

        self._lock = threading.Lock()
        self._stats: dict[str, SpiderStatistics] = {}
        self._start_time: datetime.datetime | None = None
        self._end_time: datetime.datetime | None = None

        self._logger = get_logger()

        self._last_upload_key: str = ""
        self._container_id: str = ""

    def open(self):
        if container_id := get_container_id():
            self._container_id = container_id

        self._start_time = datetime.datetime.now()

    def close(self):
        self._end_time = datetime.datetime.now()

        if self._stats:
            key_list = list(self._stats.keys())
            for key in key_list:
                self._upload_stat(key)

        self._logger.info("-" * 100)
        self._logger.info(f"爬虫运行时间: {self._start_time} ~ {self._end_time}")
        if self._start_time and self._end_time:
            self._logger.info(f"耗时: {(self._end_time - self._start_time).total_seconds()}s")
        self._logger.info("-" * 100)

    @staticmethod
    def _get_minute_key() -> tuple[str, str]:
        now = datetime.datetime.now()
        pre_minute = now - datetime.timedelta(minutes=1)
        return now.strftime("%Y-%m-%d %H:%M"), pre_minute.strftime("%Y-%m-%d %H:%M")

    def _increment(self) -> SpiderStatistics:
        """获取当前分钟的统计对象，上传前一分钟数据。调用方需持有 self._lock。"""
        minute_key, pre_minute_key = self._get_minute_key()
        if minute_key not in self._stats:
            self._stats[minute_key] = SpiderStatistics()
        stats = self._stats[minute_key]
        # 上传前一分钟的统计（在锁内同步上传，避免竞态）
        if pre_minute_key in self._stats:
            self._upload_stat_locked(pre_minute_key)
        return stats

    def record_download_success(self, status_code: int):
        status_code_str = str(status_code)
        with self._lock:
            stats = self._increment()
            stats.download_total += 1
            stats.download_success_count += 1
            stats.download_status[status_code_str] = stats.download_status.get(status_code_str, 0) + 1

    def record_download_fail(self, reason: str):
        """
        :param reason: 失败原因
        """
        with self._lock:
            stats = self._increment()
            stats.download_total += 1
            stats.download_fail_count += 1
            stats.download_fail_reason[reason] = stats.download_fail_reason.get(reason, 0) + 1

    def record_parse_success(self):
        with self._lock:
            stats = self._increment()
            stats.parse_success_count += 1

    def record_parse_fail(self):
        with self._lock:
            stats = self._increment()
            stats.parse_fail_count += 1

    def record_pipeline_success(self, count: int = 1):
        if not count:
            return
        with self._lock:
            stats = self._increment()
            stats.pipeline_success_count += count

    def record_pipeline_fail(self, count: int = 1):
        if not count:
            return
        with self._lock:
            stats = self._increment()
            stats.pipeline_fail_count += count

    def get_and_clear_stats(self, minute_key: str) -> SpiderStatistics | None:
        with self._lock:
            stats = self._stats.get(minute_key, None)
            if stats:
                del self._stats[minute_key]
            return stats

    def _upload_stat(self, pre_minute_key: str):
        """上传统计（加锁）。"""
        with self._lock:
            self._upload_stat_locked(pre_minute_key)

    def _upload_stat_locked(self, pre_minute_key: str):
        """上传统计（调用方需持有 self._lock）。"""
        if self._last_upload_key == pre_minute_key or pre_minute_key not in self._stats:
            return

        if not self._last_upload_key and len(self._stats) == 1:
            return

        pre_minute_stat = self._stats[pre_minute_key]
        maize_upload_model = MaizeUploadModel()
        maize_upload_model.pid = os.getpid()
        maize_upload_model.stat_time = pre_minute_key
        maize_upload_model.spider_name = self._spider_name
        if self._settings:
            maize_upload_model.project_name = self._settings.project_name
        maize_upload_model.container_id = self._container_id

        maize_upload_model_dict = maize_upload_model.model_dump()
        maize_upload_model_dict.update(pre_minute_stat.model_dump())
        self._logger.info(f"stat: {maize_upload_model_dict}")

        if not self._settings or not self._settings.maize_cob_api:
            del self._stats[pre_minute_key]
            self._last_upload_key = pre_minute_key
            return

        # 同步上传，最多重试 3 次
        for attempt in range(3):
            try:
                with httpx.Client() as client:
                    response = client.post(self._settings.maize_cob_api, json=maize_upload_model_dict)
                    self._logger.info(f"upload stat: <{response.status_code}> {response.text}")
                del self._stats[pre_minute_key]
                self._last_upload_key = pre_minute_key
                break
            except Exception as e:
                self._logger.warning(f"upload stat error: {e}，准备第 {attempt + 1} 次重试")

    def idle(self) -> bool:
        """同步版无后台任务，始终空闲。"""
        return True
