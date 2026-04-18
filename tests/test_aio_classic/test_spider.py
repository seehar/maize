"""
Tests for classic spider
"""

from unittest.mock import MagicMock

import pytest

from maize import SpiderSettings
from maize.aio.classic.spider.spider import Spider
from maize.common.http import Request, Response
from maize.utils.log_util import set_spider_settings


class SampleSpider(Spider):
    """Sample spider for testing"""

    async def start_requests(self):
        yield Request("https://example.com")

    async def parse(self, response: Response):
        pass


class TestSpider:
    """Test Spider class"""

    @staticmethod
    def setup_method():
        """Set up spider settings"""
        settings = SpiderSettings()
        set_spider_settings(settings)

    @pytest.fixture
    def spider(self):
        """Create a sample spider"""
        return SampleSpider()

    def test_spider_init(self, spider):
        """Test spider initialization"""
        assert spider.crawler is None
        assert spider.stats_collector is None
        assert spider.logger is None
        assert spider.gte_priority is None
        assert spider.__spider_type__ == "spider"

    def test_spider_is_abstract(self):
        """Test that Spider.start_requests is abstract"""
        assert Spider.start_requests.__isabstractmethod__ is True

    @pytest.mark.asyncio
    async def test_spider_open(self, spider):
        """Test spider open"""
        await spider.open()

        assert spider.logger is not None
        assert spider.stats_collector is not None

    @pytest.mark.asyncio
    async def test_spider_close(self, spider):
        """Test spider close"""
        await spider.open()
        await spider.close()

        # Stats collector should be closed

    @pytest.mark.asyncio
    async def test_spider_pause(self, spider):
        """Test spider pause"""
        await spider.open()

        await spider.pause_spider()

        assert spider.gte_priority == 0
        assert spider.is_pause() is True

    @pytest.mark.asyncio
    async def test_spider_pause_with_priority(self, spider):
        """Test spider pause with priority"""
        await spider.open()

        await spider.pause_spider(lte_priority=5)

        assert spider.gte_priority == 6
        assert spider.is_pause() is True

    @pytest.mark.asyncio
    async def test_spider_pause_twice(self, spider):
        """Test spider pause twice logs warning"""
        await spider.open()

        await spider.pause_spider()
        # Second pause should log warning but not change priority
        await spider.pause_spider()

        assert spider.gte_priority == 0

    @pytest.mark.asyncio
    async def test_spider_proceed(self, spider):
        """Test spider proceed"""
        await spider.open()
        await spider.pause_spider()
        assert spider.is_pause() is True

        await spider.proceed_spider()

        assert spider.gte_priority is None
        assert spider.is_pause() is False

    @pytest.mark.asyncio
    async def test_spider_proceed_with_priority(self, spider):
        """Test spider proceed with priority"""
        await spider.open()
        await spider.pause_spider(lte_priority=5)

        await spider.proceed_spider(gte_priority=3)

        assert spider.gte_priority == 3
        assert spider.is_pause() is True

    def test_spider_is_pause(self, spider):
        """Test is_pause method"""
        assert spider.is_pause() is False

        spider.gte_priority = 0

        assert spider.is_pause() is True

    def test_spider_idle(self, spider):
        """Test idle method when not paused"""
        spider.stats_collector = MagicMock()
        spider.stats_collector.idle.return_value = True
        spider.gte_priority = None

        assert spider.idle() is True

    def test_spider_idle_when_paused(self, spider):
        """Test idle method when paused"""
        spider.stats_collector = MagicMock()
        spider.stats_collector.idle.return_value = True
        spider.gte_priority = 0

        assert spider.idle() is False
