"""同步统计收集器单元测试。

覆盖 SyncStatsCollector 的所有分支：
- open/close 生命周期
- record_* 方法
- _increment 分钟切换和上传触发
- _maybe_upload 重试逻辑
- _upload_stat
- get_and_clear_stats
"""

from unittest.mock import MagicMock, patch

import pytest

from maize import SpiderSettings
from maize.sync.classic.stats.sync_stats_collector import SyncStatsCollector
from maize.utils.log_util import set_spider_settings


@pytest.fixture(autouse=True)
def _setup():
    set_spider_settings(SpiderSettings())


class TestSyncStatsCollectorLifecycle:
    def test_open_sets_start_time(self):
        collector = SyncStatsCollector("test_spider")
        collector.open()
        assert collector._start_time is not None

    def test_open_with_container_id(self):
        with patch("maize.sync.classic.stats.sync_stats_collector.get_container_id", return_value="abc123"):
            collector = SyncStatsCollector("test_spider")
            collector.open()
            assert collector._container_id == "abc123"

    def test_close_prints_summary(self):
        collector = SyncStatsCollector("test_spider")
        collector.open()
        collector.close()
        assert collector._end_time is not None

    def test_close_uploads_remaining_stats(self):
        collector = SyncStatsCollector("test_spider")
        collector.open()
        collector.record_download_success(200)
        # Force a stat entry
        assert len(collector._stats) > 0
        collector.close()

    def test_close_with_upload_client(self):
        settings = SpiderSettings()
        settings.maize_cob_api = "http://localhost:9999/upload"
        set_spider_settings(settings)
        collector = SyncStatsCollector("test_spider")
        collector.open()
        assert collector._upload_client is not None
        collector.close()
        assert collector._upload_client is None


class TestSyncStatsCollectorRecord:
    def test_record_download_success(self):
        collector = SyncStatsCollector("test_spider")
        collector.open()
        collector.record_download_success(200)
        collector.record_download_success(404)
        minute_key, _ = collector._get_minute_key()
        stats = collector._stats[minute_key]
        assert stats.download_total == 2
        assert stats.download_success_count == 2
        assert stats.download_status["200"] == 1
        assert stats.download_status["404"] == 1

    def test_record_download_fail(self):
        collector = SyncStatsCollector("test_spider")
        collector.open()
        collector.record_download_fail("timeout")
        collector.record_download_fail("timeout")
        collector.record_download_fail("dns_error")
        minute_key, _ = collector._get_minute_key()
        stats = collector._stats[minute_key]
        assert stats.download_total == 3
        assert stats.download_fail_count == 3
        assert stats.download_fail_reason["timeout"] == 2
        assert stats.download_fail_reason["dns_error"] == 1

    def test_record_parse_success(self):
        collector = SyncStatsCollector("test_spider")
        collector.open()
        collector.record_parse_success()
        minute_key, _ = collector._get_minute_key()
        assert collector._stats[minute_key].parse_success_count == 1

    def test_record_parse_fail(self):
        collector = SyncStatsCollector("test_spider")
        collector.open()
        collector.record_parse_fail()
        minute_key, _ = collector._get_minute_key()
        assert collector._stats[minute_key].parse_fail_count == 1

    def test_record_pipeline_success(self):
        collector = SyncStatsCollector("test_spider")
        collector.open()
        collector.record_pipeline_success(5)
        minute_key, _ = collector._get_minute_key()
        assert collector._stats[minute_key].pipeline_success_count == 5

    def test_record_pipeline_success_zero_noop(self):
        collector = SyncStatsCollector("test_spider")
        collector.open()
        collector.record_pipeline_success(0)
        assert len(collector._stats) == 0

    def test_record_pipeline_fail(self):
        collector = SyncStatsCollector("test_spider")
        collector.open()
        collector.record_pipeline_fail(3)
        minute_key, _ = collector._get_minute_key()
        assert collector._stats[minute_key].pipeline_fail_count == 3

    def test_record_pipeline_fail_zero_noop(self):
        collector = SyncStatsCollector("test_spider")
        collector.open()
        collector.record_pipeline_fail(0)
        assert len(collector._stats) == 0


class TestSyncStatsCollectorUpload:
    def test_maybe_upload_no_data(self):
        collector = SyncStatsCollector("test_spider")
        collector.open()
        collector._maybe_upload(None)  # no-op

    def test_maybe_upload_no_api(self):
        collector = SyncStatsCollector("test_spider")
        collector.open()
        collector._maybe_upload({"test": 1})  # no api configured, no-op

    def test_maybe_upload_with_api_success(self):
        settings = SpiderSettings()
        settings.maize_cob_api = "http://localhost:9999/upload"
        set_spider_settings(settings)
        collector = SyncStatsCollector("test_spider")
        collector.open()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "ok"
        with patch.object(collector._upload_client, "post", return_value=mock_response) as mock_post:
            collector._maybe_upload({"test": 1})
            mock_post.assert_called_once()

    def test_maybe_upload_retry_on_failure(self):
        settings = SpiderSettings()
        settings.maize_cob_api = "http://localhost:9999/upload"
        set_spider_settings(settings)
        collector = SyncStatsCollector("test_spider")
        collector.open()

        with patch.object(collector._upload_client, "post", side_effect=Exception("network error")):
            collector._maybe_upload({"test": 1})  # should retry 3 times without raising

    def test_maybe_upload_no_client(self):
        settings = SpiderSettings()
        settings.maize_cob_api = "http://localhost:9999/upload"
        set_spider_settings(settings)
        collector = SyncStatsCollector("test_spider")
        collector.open()
        collector._upload_client = None
        collector._maybe_upload({"test": 1})  # should return early

    def test_upload_stat(self):
        collector = SyncStatsCollector("test_spider")
        collector.open()
        collector.record_download_success(200)
        minute_key, _ = collector._get_minute_key()
        # _upload_stat with no api configured is a no-op after extracting data
        collector._upload_stat(minute_key)

    def test_upload_stat_already_uploaded(self):
        collector = SyncStatsCollector("test_spider")
        collector.open()
        collector.record_download_success(200)
        minute_key, _ = collector._get_minute_key()
        collector._last_upload_key = minute_key
        collector._upload_stat(minute_key)  # should skip

    def test_upload_stat_single_key_no_upload(self):
        collector = SyncStatsCollector("test_spider")
        collector.open()
        collector.record_download_success(200)
        minute_key, _ = collector._get_minute_key()
        # Only one key, no last_upload_key — should skip
        collector._upload_stat(minute_key)
        assert minute_key in collector._stats

    def test_get_and_clear_stats(self):
        collector = SyncStatsCollector("test_spider")
        collector.open()
        collector.record_download_success(200)
        minute_key, _ = collector._get_minute_key()
        stats = collector.get_and_clear_stats(minute_key)
        assert stats is not None
        assert stats.download_success_count == 1
        assert collector.get_and_clear_stats(minute_key) is None

    def test_idle_always_true(self):
        collector = SyncStatsCollector("test_spider")
        assert collector.idle() is True

    def test_increment_triggers_upload_on_minute_change(self):
        collector = SyncStatsCollector("test_spider")
        collector.open()
        collector.record_download_success(200)
        minute_key, pre_minute_key = collector._get_minute_key()
        # 把当前分钟数据伪装成“上一分钟”，触发下一次 record 时提取上传
        collector._stats[pre_minute_key] = collector._stats.pop(minute_key)
        collector._last_upload_key = ""
        collector.record_download_success(200)
        assert pre_minute_key not in collector._stats
