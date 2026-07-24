"""StatsCollector upload_stat 内部协程重试路径测试。

现有 test_stats_upload.py mock 了 create_task，导致内部 upload_stat() 协程
（stats_collector.py:197-207 的重试循环）从未真正执行。本测试捕获该协程并
实际运行，覆盖成功/重试 3 次两条路径。
"""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from maize.core.stats.stats_collector import StatsCollector


def _make_collector(maize_cob_api="http://api.example.com/upload"):
    mock_settings = MagicMock()
    mock_settings.project_name = "test_project"
    mock_settings.maize_cob_api = maize_cob_api
    mock_logger = MagicMock()

    with (
        patch("maize.core.stats.stats_collector.get_spider_settings", return_value=mock_settings),
        patch("maize.core.stats.stats_collector.get_logger", return_value=mock_logger),
        patch("maize.core.stats.stats_collector.get_container_id", return_value="container-123"),
    ):
        return StatsCollector("test_spider")


class TestUploadStatCoroutine:
    """实际执行内部 upload_stat() 协程，覆盖重试循环。"""

    @pytest.mark.asyncio
    async def test_upload_success_deletes_key(self):
        """上传成功后删除 stat 并更新 last_upload_key。"""
        collector = _make_collector()
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
            # 捕获并执行内部协程
            coro = collector._task_manager.create_task.call_args[0][0]
            await coro

        assert minute_key not in collector._stats
        assert collector._last_upload_key == minute_key
        assert mock_client.post.call_count == 1

    @pytest.mark.asyncio
    async def test_upload_retries_three_times_then_gives_up(self):
        """上传持续失败时重试 3 次，stat 不被删除。"""
        collector = _make_collector()
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
            coro = collector._task_manager.create_task.call_args[0][0]
            await coro

        # 3 次重试全部失败，stat 保留
        assert mock_client.post.call_count == 3
        assert minute_key in collector._stats
