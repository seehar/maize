"""
Tests for SpiderEntry decorator entry point.
"""

from typing import ClassVar
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from maize.core.decorator_entry import SpiderEntry


class TestSpiderEntry:
    """Test SpiderEntry register and run."""

    def test_init_empty(self):
        entry = SpiderEntry()
        assert entry.spider_list == []

    def test_register_appends_spider(self):
        entry = SpiderEntry()

        class MySpider:
            pass

        decorator = entry.register()
        result = decorator(MySpider)
        assert result is MySpider
        assert MySpider in entry.spider_list
        assert len(entry.spider_list) == 1

    def test_register_with_settings_no_existing_custom(self):
        entry = SpiderEntry()

        class MySpider:
            pass

        entry.register(settings={"concurrency": 5})(MySpider)
        assert MySpider.custom_settings == {"concurrency": 5}

    def test_register_with_settings_existing_custom(self):
        entry = SpiderEntry()

        class MySpider:
            custom_settings: ClassVar[dict] = {"project_name": "test"}

        entry.register(settings={"concurrency": 5})(MySpider)
        assert MySpider.custom_settings["concurrency"] == 5
        assert MySpider.custom_settings["project_name"] == "test"

    def test_register_without_settings(self):
        """Register without settings does not set custom_settings."""
        entry = SpiderEntry()

        class MySpider:
            pass

        entry.register()(MySpider)
        assert not hasattr(MySpider, "custom_settings")

    def test_get_spider_list(self):
        entry = SpiderEntry()

        class A:
            pass

        class B:
            pass

        entry.register()(A)
        entry.register()(B)
        result = entry.get_spider_list()
        assert A in result
        assert B in result
        assert len(result) == 2

    def test_run_calls_asyncio_run(self):
        entry = SpiderEntry()
        with patch("maize.core.decorator_entry.asyncio.run") as mock_run:
            entry.run()
            mock_run.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_async_creates_crawler_process(self):
        entry = SpiderEntry()

        class MySpider:
            pass

        entry.register()(MySpider)

        with patch("maize.core.decorator_entry.CrawlerProcess") as mock_proc_cls:
            mock_proc = MagicMock()
            mock_proc.crawl = AsyncMock()
            mock_proc.start = AsyncMock()
            mock_proc_cls.return_value = mock_proc

            await entry.run_async()
            mock_proc_cls.assert_called_once()
            mock_proc.crawl.assert_called_once_with(MySpider)
            mock_proc.start.assert_called_once()
