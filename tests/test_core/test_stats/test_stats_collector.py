"""
Tests for StatsCollector
"""

from unittest.mock import MagicMock, patch

import pytest

from maize.core.stats.stats_collector import StatsCollector


class TestStatsCollector:
    """Test StatsCollector"""

    @pytest.fixture
    def mock_settings(self):
        settings = MagicMock()
        settings.project_name = "test_project"
        settings.maize_cob_api = None
        return settings

    @pytest.fixture
    def mock_logger(self):
        return MagicMock()

    @pytest.fixture
    def stats_collector(self, mock_settings, mock_logger):
        with (
            patch("maize.core.stats.stats_collector.get_spider_settings", return_value=mock_settings),
            patch("maize.core.stats.stats_collector.get_logger", return_value=mock_logger),
            patch("maize.core.stats.stats_collector.get_container_id", return_value=None),
        ):
            return StatsCollector("test_spider")

    @pytest.mark.asyncio
    async def test_open_with_container_id(self):
        """Test open with container_id"""
        mock_settings = MagicMock()
        mock_settings.project_name = "test_project"
        mock_settings.maize_cob_api = None
        mock_logger = MagicMock()

        with (
            patch("maize.core.stats.stats_collector.get_spider_settings", return_value=mock_settings),
            patch("maize.core.stats.stats_collector.get_logger", return_value=mock_logger),
            patch("maize.core.stats.stats_collector.get_container_id", return_value="container-123"),
        ):
            collector = StatsCollector("test_spider")
            await collector.open()

            assert collector._container_id == "container-123"
            assert collector._start_time is not None

    @pytest.mark.asyncio
    async def test_open_without_container_id(self):
        """Test open without container_id"""
        mock_settings = MagicMock()
        mock_settings.project_name = "test_project"
        mock_settings.maize_cob_api = None
        mock_logger = MagicMock()

        with (
            patch("maize.core.stats.stats_collector.get_spider_settings", return_value=mock_settings),
            patch("maize.core.stats.stats_collector.get_logger", return_value=mock_logger),
            patch("maize.core.stats.stats_collector.get_container_id", return_value=None),
        ):
            collector = StatsCollector("test_spider")
            await collector.open()

            assert collector._container_id == ""
            assert collector._start_time is not None

    @pytest.mark.asyncio
    async def test_close_with_stats(self):
        """Test close with stats"""
        mock_settings = MagicMock()
        mock_settings.project_name = "test_project"
        mock_settings.maize_cob_api = None
        mock_logger = MagicMock()
        mock_logger.info = MagicMock()
        mock_logger.warning = MagicMock()

        with (
            patch("maize.core.stats.stats_collector.get_spider_settings", return_value=mock_settings),
            patch("maize.core.stats.stats_collector.get_logger", return_value=mock_logger),
            patch("maize.core.stats.stats_collector.get_container_id", return_value=None),
        ):
            collector = StatsCollector("test_spider")
            await collector.open()
            await collector.close()

            assert collector._end_time is not None

    @pytest.mark.asyncio
    async def test_record_download_success(self):
        """Test record_download_success"""
        mock_settings = MagicMock()
        mock_settings.project_name = "test_project"
        mock_settings.maize_cob_api = None
        mock_logger = MagicMock()

        with (
            patch("maize.core.stats.stats_collector.get_spider_settings", return_value=mock_settings),
            patch("maize.core.stats.stats_collector.get_logger", return_value=mock_logger),
            patch("maize.core.stats.stats_collector.get_container_id", return_value=None),
        ):
            collector = StatsCollector("test_spider")
            await collector.open()
            await collector.record_download_success(200)

            minute_key, _ = StatsCollector._get_minute_key()
            assert minute_key in collector._stats
            stats = collector._stats[minute_key]
            assert stats.download_success_count == 1
            assert stats.download_total == 1
            assert "200" in stats.download_status

    @pytest.mark.asyncio
    async def test_record_download_success_multiple_status_codes(self):
        """Test record_download_success with multiple status codes"""
        mock_settings = MagicMock()
        mock_settings.project_name = "test_project"
        mock_settings.maize_cob_api = None
        mock_logger = MagicMock()

        with (
            patch("maize.core.stats.stats_collector.get_spider_settings", return_value=mock_settings),
            patch("maize.core.stats.stats_collector.get_logger", return_value=mock_logger),
            patch("maize.core.stats.stats_collector.get_container_id", return_value=None),
        ):
            collector = StatsCollector("test_spider")
            await collector.open()
            await collector.record_download_success(200)
            await collector.record_download_success(200)
            await collector.record_download_success(404)

            minute_key, _ = StatsCollector._get_minute_key()
            stats = collector._stats[minute_key]
            assert stats.download_success_count == 3
            assert stats.download_status["200"] == 2
            assert stats.download_status["404"] == 1

    @pytest.mark.asyncio
    async def test_record_download_fail(self):
        """Test record_download_fail"""
        mock_settings = MagicMock()
        mock_settings.project_name = "test_project"
        mock_settings.maize_cob_api = None
        mock_logger = MagicMock()

        with (
            patch("maize.core.stats.stats_collector.get_spider_settings", return_value=mock_settings),
            patch("maize.core.stats.stats_collector.get_logger", return_value=mock_logger),
            patch("maize.core.stats.stats_collector.get_container_id", return_value=None),
        ):
            collector = StatsCollector("test_spider")
            await collector.open()
            await collector.record_download_fail("ConnectionError")

            minute_key, _ = StatsCollector._get_minute_key()
            stats = collector._stats[minute_key]
            assert stats.download_fail_count == 1
            assert stats.download_total == 1
            assert "ConnectionError" in stats.download_fail_reason

    @pytest.mark.asyncio
    async def test_record_download_fail_multiple_reasons(self):
        """Test record_download_fail with multiple reasons"""
        mock_settings = MagicMock()
        mock_settings.project_name = "test_project"
        mock_settings.maize_cob_api = None
        mock_logger = MagicMock()

        with (
            patch("maize.core.stats.stats_collector.get_spider_settings", return_value=mock_settings),
            patch("maize.core.stats.stats_collector.get_logger", return_value=mock_logger),
            patch("maize.core.stats.stats_collector.get_container_id", return_value=None),
        ):
            collector = StatsCollector("test_spider")
            await collector.open()
            await collector.record_download_fail("Timeout")
            await collector.record_download_fail("Timeout")
            await collector.record_download_fail("ConnectionRefused")

            minute_key, _ = StatsCollector._get_minute_key()
            stats = collector._stats[minute_key]
            assert stats.download_fail_count == 3
            assert stats.download_fail_reason["Timeout"] == 2
            assert stats.download_fail_reason["ConnectionRefused"] == 1

    @pytest.mark.asyncio
    async def test_record_parse_success(self):
        """Test record_parse_success"""
        mock_settings = MagicMock()
        mock_settings.project_name = "test_project"
        mock_settings.maize_cob_api = None
        mock_logger = MagicMock()

        with (
            patch("maize.core.stats.stats_collector.get_spider_settings", return_value=mock_settings),
            patch("maize.core.stats.stats_collector.get_logger", return_value=mock_logger),
            patch("maize.core.stats.stats_collector.get_container_id", return_value=None),
        ):
            collector = StatsCollector("test_spider")
            await collector.open()
            await collector.record_parse_success()

            minute_key, _ = StatsCollector._get_minute_key()
            stats = collector._stats[minute_key]
            assert stats.parse_success_count == 1

    @pytest.mark.asyncio
    async def test_record_parse_fail(self):
        """Test record_parse_fail"""
        mock_settings = MagicMock()
        mock_settings.project_name = "test_project"
        mock_settings.maize_cob_api = None
        mock_logger = MagicMock()

        with (
            patch("maize.core.stats.stats_collector.get_spider_settings", return_value=mock_settings),
            patch("maize.core.stats.stats_collector.get_logger", return_value=mock_logger),
            patch("maize.core.stats.stats_collector.get_container_id", return_value=None),
        ):
            collector = StatsCollector("test_spider")
            await collector.open()
            await collector.record_parse_fail()

            minute_key, _ = StatsCollector._get_minute_key()
            stats = collector._stats[minute_key]
            assert stats.parse_fail_count == 1

    @pytest.mark.asyncio
    async def test_record_pipeline_success(self):
        """Test record_pipeline_success"""
        mock_settings = MagicMock()
        mock_settings.project_name = "test_project"
        mock_settings.maize_cob_api = None
        mock_logger = MagicMock()

        with (
            patch("maize.core.stats.stats_collector.get_spider_settings", return_value=mock_settings),
            patch("maize.core.stats.stats_collector.get_logger", return_value=mock_logger),
            patch("maize.core.stats.stats_collector.get_container_id", return_value=None),
        ):
            collector = StatsCollector("test_spider")
            await collector.open()
            await collector.record_pipeline_success(5)

            minute_key, _ = StatsCollector._get_minute_key()
            stats = collector._stats[minute_key]
            assert stats.pipeline_success_count == 5

    @pytest.mark.asyncio
    async def test_record_pipeline_success_zero_count(self):
        """Test record_pipeline_success with zero count"""
        mock_settings = MagicMock()
        mock_settings.project_name = "test_project"
        mock_settings.maize_cob_api = None
        mock_logger = MagicMock()

        with (
            patch("maize.core.stats.stats_collector.get_spider_settings", return_value=mock_settings),
            patch("maize.core.stats.stats_collector.get_logger", return_value=mock_logger),
            patch("maize.core.stats.stats_collector.get_container_id", return_value=None),
        ):
            collector = StatsCollector("test_spider")
            await collector.open()
            await collector.record_pipeline_success(0)

            minute_key, _ = StatsCollector._get_minute_key()
            assert minute_key not in collector._stats

    @pytest.mark.asyncio
    async def test_record_pipeline_fail(self):
        """Test record_pipeline_fail"""
        mock_settings = MagicMock()
        mock_settings.project_name = "test_project"
        mock_settings.maize_cob_api = None
        mock_logger = MagicMock()

        with (
            patch("maize.core.stats.stats_collector.get_spider_settings", return_value=mock_settings),
            patch("maize.core.stats.stats_collector.get_logger", return_value=mock_logger),
            patch("maize.core.stats.stats_collector.get_container_id", return_value=None),
        ):
            collector = StatsCollector("test_spider")
            await collector.open()
            await collector.record_pipeline_fail(3)

            minute_key, _ = StatsCollector._get_minute_key()
            stats = collector._stats[minute_key]
            assert stats.pipeline_fail_count == 3

    @pytest.mark.asyncio
    async def test_record_pipeline_fail_zero_count(self):
        """Test record_pipeline_fail with zero count"""
        mock_settings = MagicMock()
        mock_settings.project_name = "test_project"
        mock_settings.maize_cob_api = None
        mock_logger = MagicMock()

        with (
            patch("maize.core.stats.stats_collector.get_spider_settings", return_value=mock_settings),
            patch("maize.core.stats.stats_collector.get_logger", return_value=mock_logger),
            patch("maize.core.stats.stats_collector.get_container_id", return_value=None),
        ):
            collector = StatsCollector("test_spider")
            await collector.open()
            await collector.record_pipeline_fail(0)

            minute_key, _ = StatsCollector._get_minute_key()
            assert minute_key not in collector._stats

    @pytest.mark.asyncio
    async def test_get_and_clear_stats(self):
        """Test get_and_clear_stats"""
        mock_settings = MagicMock()
        mock_settings.project_name = "test_project"
        mock_settings.maize_cob_api = None
        mock_logger = MagicMock()

        with (
            patch("maize.core.stats.stats_collector.get_spider_settings", return_value=mock_settings),
            patch("maize.core.stats.stats_collector.get_logger", return_value=mock_logger),
            patch("maize.core.stats.stats_collector.get_container_id", return_value=None),
        ):
            collector = StatsCollector("test_spider")
            await collector.open()
            await collector.record_download_success(200)

            minute_key, _ = StatsCollector._get_minute_key()
            stats = await collector.get_and_clear_stats(minute_key)

            assert stats is not None
            assert stats.download_success_count == 1
            assert minute_key not in collector._stats

    @pytest.mark.asyncio
    async def test_get_and_clear_stats_not_found(self):
        """Test get_and_clear_stats when key not found"""
        mock_settings = MagicMock()
        mock_settings.project_name = "test_project"
        mock_settings.maize_cob_api = None
        mock_logger = MagicMock()

        with (
            patch("maize.core.stats.stats_collector.get_spider_settings", return_value=mock_settings),
            patch("maize.core.stats.stats_collector.get_logger", return_value=mock_logger),
            patch("maize.core.stats.stats_collector.get_container_id", return_value=None),
        ):
            collector = StatsCollector("test_spider")
            await collector.open()

            stats = await collector.get_and_clear_stats("non-existent-key")

            assert stats is None

    def test_get_minute_key(self):
        """Test _get_minute_key"""
        now_key, pre_minute_key = StatsCollector._get_minute_key()

        assert now_key is not None
        assert pre_minute_key is not None
        assert now_key != pre_minute_key

    @pytest.mark.asyncio
    async def test_idle(self):
        """Test idle method"""
        mock_settings = MagicMock()
        mock_settings.project_name = "test_project"
        mock_settings.maize_cob_api = None
        mock_logger = MagicMock()

        with (
            patch("maize.core.stats.stats_collector.get_spider_settings", return_value=mock_settings),
            patch("maize.core.stats.stats_collector.get_logger", return_value=mock_logger),
            patch("maize.core.stats.stats_collector.get_container_id", return_value=None),
        ):
            collector = StatsCollector("test_spider")
            await collector.open()

            assert collector.idle() is True

    @pytest.mark.asyncio
    async def test_upload_stat_same_key(self):
        """Test _upload_stat skips when key matches last upload"""
        mock_settings = MagicMock()
        mock_settings.project_name = "test_project"
        mock_settings.maize_cob_api = None
        mock_logger = MagicMock()
        mock_logger.info = MagicMock()

        with (
            patch("maize.core.stats.stats_collector.get_spider_settings", return_value=mock_settings),
            patch("maize.core.stats.stats_collector.get_logger", return_value=mock_logger),
            patch("maize.core.stats.stats_collector.get_container_id", return_value=None),
        ):
            collector = StatsCollector("test_spider")
            collector._last_upload_key = "2024-01-01 12:00"

            # This should return early because pre_minute_key == _last_upload_key
            await collector._upload_stat("2024-01-01 12:00")

    @pytest.mark.asyncio
    async def test_upload_stat_key_not_in_stats(self):
        """Test _upload_stat skips when key not in stats"""
        mock_settings = MagicMock()
        mock_settings.project_name = "test_project"
        mock_settings.maize_cob_api = None
        mock_logger = MagicMock()
        mock_logger.info = MagicMock()

        with (
            patch("maize.core.stats.stats_collector.get_spider_settings", return_value=mock_settings),
            patch("maize.core.stats.stats_collector.get_logger", return_value=mock_logger),
            patch("maize.core.stats.stats_collector.get_container_id", return_value=None),
        ):
            collector = StatsCollector("test_spider")

            # This should return early because key not in stats
            await collector._upload_stat("2024-01-01 12:00")

    @pytest.mark.asyncio
    async def test_upload_stat_only_one_stat(self):
        """Test _upload_stat skips when only one stat exists"""
        mock_settings = MagicMock()
        mock_settings.project_name = "test_project"
        mock_settings.maize_cob_api = None
        mock_logger = MagicMock()
        mock_logger.info = MagicMock()

        with (
            patch("maize.core.stats.stats_collector.get_spider_settings", return_value=mock_settings),
            patch("maize.core.stats.stats_collector.get_logger", return_value=mock_logger),
            patch("maize.core.stats.stats_collector.get_container_id", return_value=None),
        ):
            collector = StatsCollector("test_spider")
            await collector.open()

            minute_key, _ = StatsCollector._get_minute_key()

            # This should return early because only one stat and no last_upload_key
            await collector._upload_stat(minute_key)

    @pytest.mark.asyncio
    async def test_upload_stat_no_api(self):
        """Test _upload_stat without API uploads stat and updates key"""
        mock_settings = MagicMock()
        mock_settings.project_name = "test_project"
        mock_settings.maize_cob_api = None
        mock_logger = MagicMock()
        mock_logger.info = MagicMock()

        with (
            patch("maize.core.stats.stats_collector.get_spider_settings", return_value=mock_settings),
            patch("maize.core.stats.stats_collector.get_logger", return_value=mock_logger),
            patch("maize.core.stats.stats_collector.get_container_id", return_value=None),
            patch("maize.core.stats.stats_collector.os.getpid", return_value=12345),
        ):
            collector = StatsCollector("test_spider")
            await collector.open()
            await collector.record_download_success(200)

            minute_key, _pre_minute_key = StatsCollector._get_minute_key()

            # Create another stat entry to avoid the "only one stat" early return
            collector._stats["dummy_key"] = collector._stats[minute_key]

            await collector._upload_stat(minute_key)

            assert collector._last_upload_key == minute_key
            assert minute_key not in collector._stats
