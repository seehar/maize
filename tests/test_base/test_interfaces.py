"""
Tests for SpiderInterface and LiteSpiderInterface abstract methods.
"""

from unittest.mock import MagicMock

import pytest

from maize.base.interface.lite_spider_interface import LiteSpiderInterface
from maize.base.interface.spider_interface import SpiderInterface
from maize.base.interface.standard_spider_interface import StandardSpiderInterface


class TestSpiderInterface:
    """Test SpiderInterface abstract contract."""

    def test_cannot_instantiate_directly(self):
        with pytest.raises(TypeError):
            SpiderInterface()

    def test_str_returns_class_name(self):
        """__str__ returns class name — test via a concrete subclass."""

        class MySpider(SpiderInterface):
            async def open(self):
                pass

            async def close(self):
                pass

            def start_requests(self):
                pass

            def parse(self, response):
                pass

        spider = MySpider()
        assert str(spider) == "MySpider"


class TestLiteSpiderInterface:
    """Test LiteSpiderInterface abstract contract."""

    def test_cannot_instantiate_directly(self):
        with pytest.raises(TypeError):
            LiteSpiderInterface()

    def test_default_concurrency(self):
        class MyLite(LiteSpiderInterface):
            async def start_requests(self):
                pass

            async def parse(self, response):
                pass

        spider = MyLite()
        assert spider.concurrency == 5

    def test_default_retry(self):
        class MyLite(LiteSpiderInterface):
            async def start_requests(self):
                pass

            async def parse(self, response):
                pass

        spider = MyLite()
        assert spider.retry == 3

    def test_default_proxy(self):
        class MyLite(LiteSpiderInterface):
            async def start_requests(self):
                pass

            async def parse(self, response):
                pass

        spider = MyLite()
        assert spider.proxy is None

    def test_default_timeout(self):
        class MyLite(LiteSpiderInterface):
            async def start_requests(self):
                pass

            async def parse(self, response):
                pass

        spider = MyLite()
        assert spider.timeout == 30.0


class TestStandardSpiderInterface:
    """Test StandardSpiderInterface."""

    def test_cannot_instantiate_directly(self):
        with pytest.raises(TypeError):
            StandardSpiderInterface()

    def test_default_idle(self):
        class MySpider(StandardSpiderInterface):
            __spider_type__ = "spider"

            async def open(self):
                pass

            async def close(self):
                pass

            def start_requests(self):
                pass

            def parse(self, response):
                pass

        spider = MySpider()
        assert spider.idle() is True

    def test_create_instance_sets_crawler(self):
        class MySpider(StandardSpiderInterface):
            __spider_type__ = "spider"

            async def open(self):
                pass

            async def close(self):
                pass

            def start_requests(self):
                pass

            def parse(self, response):
                pass

        crawler = MagicMock()
        instance = MySpider.create_instance(crawler)
        assert instance.crawler is crawler
