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
        """
        初始化同步统计收集器。

        :param spider_name: Spider 名称，用于上报标识
        """
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
        """
        打开统计收集器，记录容器 ID 和启动时间。
        """
        if container_id := get_container_id():
            self._container_id = container_id

        self._start_time = datetime.datetime.now()

    def close(self):
        """
        关闭统计收集器，上报剩余统计数据并打印运行时间摘要。
        """
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

    def _increment(self) -> tuple[SpiderStatistics, dict | None]:
        """获取当前分钟的统计对象，提取前一分钟待上传数据。调用方需持有 self._lock。

        :returns: (当前分钟统计对象, 待上传数据 dict 或 None)
        """
        minute_key, pre_minute_key = self._get_minute_key()
        if minute_key not in self._stats:
            self._stats[minute_key] = SpiderStatistics()
        stats = self._stats[minute_key]
        # 提取前一分钟的统计数据，在锁外上传
        upload_data = None
        if (
            pre_minute_key in self._stats
            and self._last_upload_key != pre_minute_key
            and (self._last_upload_key or len(self._stats) > 1)
        ):
            pre_minute_stat = self._stats.pop(pre_minute_key)
            self._last_upload_key = pre_minute_key
            upload_data = self._build_upload_dict(pre_minute_key, pre_minute_stat)
        return stats, upload_data

    def _build_upload_dict(self, minute_key: str, stat: SpiderStatistics) -> dict:
        """构建上传数据 dict（纯数据准备，无 IO）。"""
        maize_upload_model = MaizeUploadModel()
        maize_upload_model.pid = os.getpid()
        maize_upload_model.stat_time = minute_key
        maize_upload_model.spider_name = self._spider_name
        if self._settings:
            maize_upload_model.project_name = self._settings.project_name
        maize_upload_model.container_id = self._container_id
        maize_upload_model_dict = maize_upload_model.model_dump()
        maize_upload_model_dict.update(stat.model_dump())
        return maize_upload_model_dict

    def _maybe_upload(self, upload_data: dict | None):
        """在锁外执行上传（无锁）。"""
        if upload_data is None:
            return
        self._logger.info(f"stat: {upload_data}")
        if not self._settings or not self._settings.maize_cob_api:
            return
        for attempt in range(3):
            try:
                with httpx.Client() as client:
                    response = client.post(self._settings.maize_cob_api, json=upload_data)
                    self._logger.info(f"upload stat: <{response.status_code}> {response.text}")
                break
            except Exception as e:
                self._logger.warning(f"upload stat error: {e}，准备第 {attempt + 1} 次重试")

    def record_download_success(self, status_code: int):
        """
        记录一次下载成功，按状态码分类计数。

        :param status_code: HTTP 响应状态码
        """
        status_code_str = str(status_code)
        with self._lock:
            stats, upload_data = self._increment()
            stats.download_total += 1
            stats.download_success_count += 1
            stats.download_status[status_code_str] = stats.download_status.get(status_code_str, 0) + 1
        self._maybe_upload(upload_data)

    def record_download_fail(self, reason: str):
        """
        :param reason: 失败原因
        """
        with self._lock:
            stats, upload_data = self._increment()
            stats.download_total += 1
            stats.download_fail_count += 1
            stats.download_fail_reason[reason] = stats.download_fail_reason.get(reason, 0) + 1
        self._maybe_upload(upload_data)

    def record_parse_success(self):
        """
        记录一次解析成功。
        """
        with self._lock:
            stats, upload_data = self._increment()
            stats.parse_success_count += 1
        self._maybe_upload(upload_data)

    def record_parse_fail(self):
        """
        记录一次解析失败。
        """
        with self._lock:
            stats, upload_data = self._increment()
            stats.parse_fail_count += 1
        self._maybe_upload(upload_data)

    def record_pipeline_success(self, count: int = 1):
        """
        记录管道处理成功的数据条数。

        :param count: 成功条数，默认 1，为 0 时直接返回
        """
        if not count:
            return
        with self._lock:
            stats, upload_data = self._increment()
            stats.pipeline_success_count += count
        self._maybe_upload(upload_data)

    def record_pipeline_fail(self, count: int = 1):
        """
        记录管道处理失败的数据条数。

        :param count: 失败条数，默认 1，为 0 时直接返回
        """
        if not count:
            return
        with self._lock:
            stats, upload_data = self._increment()
            stats.pipeline_fail_count += count
        self._maybe_upload(upload_data)

    def get_and_clear_stats(self, minute_key: str) -> SpiderStatistics | None:
        """
        获取并清除指定分钟的统计数据。

        :param minute_key: 分钟键（``YYYY-MM-DD HH:MM`` 格式）
        :return: 统计数据，不存在则返回 None
        """
        with self._lock:
            stats = self._stats.get(minute_key, None)
            if stats:
                del self._stats[minute_key]
            return stats

    def _upload_stat(self, pre_minute_key: str):
        """上传统计（加锁提取数据，锁外上传）。"""
        with self._lock:
            if self._last_upload_key == pre_minute_key or pre_minute_key not in self._stats:
                return
            if not self._last_upload_key and len(self._stats) == 1:
                return
            pre_minute_stat = self._stats.pop(pre_minute_key)
            self._last_upload_key = pre_minute_key
            upload_data = self._build_upload_dict(pre_minute_key, pre_minute_stat)
        self._maybe_upload(upload_data)

    def idle(self) -> bool:
        """同步版无后台任务，始终空闲。"""
        return True
