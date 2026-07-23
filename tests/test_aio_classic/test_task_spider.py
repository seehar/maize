"""
Tests for TaskSpider.
"""

import inspect
from unittest.mock import MagicMock

import pytest

from maize.aio.classic.spider.spider import Spider
from maize.aio.classic.spider.task_spider import TaskSpider
from maize.common.http.request import Request


class SimpleTaskSpider(TaskSpider):
    """Minimal TaskSpider for testing."""

    async def start_requests(self):
        yield Request("https://example.com")


class TestTaskSpider:
    """Test TaskSpider."""

    def test_spider_type(self):
        spider = SimpleTaskSpider()
        assert spider.__spider_type__ == "task_spider"

    def test_inherits_from_spider(self):
        assert issubclass(TaskSpider, Spider)

    def test_start_requests_is_abstract(self):
        """TaskSpider.start_requests is abstract."""
        assert TaskSpider.start_requests.__isabstractmethod__ is True

    def test_instance_with_implementation(self):
        """A concrete subclass can be instantiated."""
        spider = SimpleTaskSpider()
        assert spider is not None
        assert spider.__spider_type__ == "task_spider"

    @pytest.mark.asyncio
    async def test_start_requests_yields_request(self):
        spider = SimpleTaskSpider()
        spider.crawler = MagicMock()
        results = []
        async for req in spider.start_requests():
            results.append(req)
        assert len(results) == 1
        assert isinstance(results[0], Request)

    @pytest.mark.asyncio
    async def test_base_task_spider_start_requests_yields_empty(self):
        """The base TaskSpider.start_requests yields Request('')."""
        # We can't instantiate TaskSpider directly (abstract), but we can
        # verify its default implementation yields an empty-url Request
        source = inspect.getsource(TaskSpider.start_requests)
        assert "yield" in source
        assert 'Request("")' in source
