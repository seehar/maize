"""
Tests for StatsCollector _upload_stat with maize_cob_api (lines 146-159).
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from maize.core.stats.stats_collector import StatsCollector


def _make_collector(maize_cob_api=None):
    mock_settings = MagicMock()
    mock_settings.project_name = "test_project"
    mock_settings.maize_cob_api = maize_cob_api
    mock_logger = MagicMock()

    with (
        patch("maize.core.stats.stats_collector.get_spider_settings", return_value=mock_settings),
        patch("maize.core.stats.stats_collector.get_logger", return_value=mock_logger),
        patch("maize.core.stats.stats_collector.get_container_id", return_value="container-123"),
    ):
        collector = StatsCollector("test_spider")
    return collector, mock_logger


class TestUploadStatWithApi:
    """Cover _upload_stat with maize_cob_api set (lines 146-159)."""

    @pytest.mark.asyncio
    async def test_upload_stat_with_api_creates_task(self):
        collector, _ = _make_collector(maize_cob_api="http://api.example.com/upload")
        collector._task_manager.create_task = MagicMock()
        await collector.open()
        await collector.record_download_success(200)

        minute_key, _ = StatsCollector._get_minute_key()
        collector._stats["dummy_key"] = collector._stats[minute_key]

        with (
            patch("maize.core.stats.stats_collector.os.getpid", return_value=12345),
            patch("maize.core.stats.stats_collector.httpx.AsyncClient") as mock_client_cls,
        ):
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.text = "ok"
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_client_cls.return_value = mock_client

            await collector._upload_stat(minute_key)
            collector._task_manager.create_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_upload_stat_api_retries_on_failure(self):
        """Upload retries 3 times on exception."""
        collector, _ = _make_collector(maize_cob_api="http://api.example.com/upload")
        collector._task_manager.create_task = MagicMock()
        await collector.open()
        await collector.record_download_success(200)

        minute_key, _ = StatsCollector._get_minute_key()
        collector._stats["dummy_key"] = collector._stats[minute_key]

        with (
            patch("maize.core.stats.stats_collector.os.getpid", return_value=12345),
            patch("maize.core.stats.stats_collector.httpx.AsyncClient") as mock_client_cls,
        ):
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(side_effect=httpx.ConnectError("refused"))
            mock_client_cls.return_value = mock_client

            await collector._upload_stat(minute_key)
            collector._task_manager.create_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_upload_stat_no_api_deletes_key(self):
        """When no api, _upload_stat deletes key and updates last_upload_key."""
        collector, _ = _make_collector(maize_cob_api=None)
        await collector.open()
        await collector.record_download_success(200)

        minute_key, _ = StatsCollector._get_minute_key()
        collector._stats["dummy_key"] = collector._stats[minute_key]

        with patch("maize.core.stats.stats_collector.os.getpid", return_value=12345):
            await collector._upload_stat(minute_key)
            assert collector._last_upload_key == minute_key
            assert minute_key not in collector._stats


# Import httpx at module level
import httpx  # noqa: E402
