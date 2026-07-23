"""
Tests for classic Crawler and CrawlerProcess.
"""

from typing import ClassVar
from unittest.mock import MagicMock

import pytest

from maize.aio.classic.crawler.crawler import Crawler, CrawlerProcess
from maize.aio.classic.spider.spider import Spider
from maize.common.http.request import Request
from maize.common.http.response import Response
from maize.exceptions.spider_exception import SpiderTypeException
from maize.settings import SpiderSettings


class SimpleSpider(Spider):
    """Minimal spider for testing."""

    async def start_requests(self):
        yield Request("https://example.com")

    async def parse(self, response: Response):
        pass


class TestCrawler:
    """Test Crawler."""

    def test_init(self):
        settings = SpiderSettings()
        crawler = Crawler(SimpleSpider, settings)
        assert crawler.spider_cls is SimpleSpider
        assert crawler.settings is settings
        assert crawler.spider is None
        assert crawler.engine is None

    def test_create_engine(self):
        settings = SpiderSettings()
        crawler = Crawler(SimpleSpider, settings)
        engine = crawler._create_engine()
        assert engine is not None
        assert engine.crawler is crawler

    def test_create_spider(self):
        settings = SpiderSettings()
        crawler = Crawler(SimpleSpider, settings)
        spider = crawler._create_spider()
        assert isinstance(spider, SimpleSpider)
        assert spider.crawler is crawler

    def test_set_spider_no_custom_settings(self):
        """_set_spider with no custom_settings does nothing."""
        settings = SpiderSettings()
        crawler = Crawler(SimpleSpider, settings)
        original_concurrency = settings.concurrency
        spider = SimpleSpider()
        crawler._set_spider(spider)
        assert settings.concurrency == original_concurrency

    def test_set_spider_with_dict_custom_settings(self):
        settings = SpiderSettings()
        crawler = Crawler(SimpleSpider, settings)

        class CustomSpider(SimpleSpider):
            custom_settings: ClassVar[dict] = {"concurrency": 10}

        spider = CustomSpider()
        crawler._set_spider(spider)
        assert settings.concurrency == 10

    def test_set_spider_with_spider_settings(self):
        settings = SpiderSettings()
        crawler = Crawler(SimpleSpider, settings)

        custom = SpiderSettings()
        custom.concurrency = 20

        class CustomSpider(SimpleSpider):
            custom_settings: ClassVar = custom

        spider = CustomSpider()
        crawler._set_spider(spider)
        assert settings.concurrency == 20

    def test_init_with_default_settings(self):
        """CrawlerProcess loads settings from a valid settings_path."""
        process = CrawlerProcess(settings_path="maize.SpiderSettings")
        assert process.settings is not None

    def test_idle(self):
        settings = SpiderSettings()
        crawler = Crawler(SimpleSpider, settings)
        crawler.spider = MagicMock()
        crawler.spider.idle.return_value = True
        assert crawler.idle() is True
        crawler.spider.idle.return_value = False
        assert crawler.idle() is False


class TestCrawlerProcess:
    """Test CrawlerProcess."""

    def test_init_with_explicit_settings(self):
        settings = SpiderSettings()
        process = CrawlerProcess(settings=settings)
        assert process.settings is settings

    def test_init_with_default_settings(self):
        process = CrawlerProcess(settings_path=None)
        assert process.settings is not None

    def test_create_crawler_with_spider_class(self):
        process = CrawlerProcess(settings=SpiderSettings())
        crawler = process._create_crawler(SimpleSpider)
        assert isinstance(crawler, Crawler)
        assert crawler.spider_cls is SimpleSpider

    def test_create_crawler_with_string_raises(self):
        """Passing a string spider_cls should raise SpiderTypeException."""
        process = CrawlerProcess(settings=SpiderSettings())
        with pytest.raises(SpiderTypeException):
            process._create_crawler("not.a.class")

    def test_crawlers_set_starts_empty(self):
        process = CrawlerProcess(settings=SpiderSettings())
        assert len(process.crawlers) == 0
        assert len(process._active) == 0
