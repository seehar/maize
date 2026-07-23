"""
Integration test: TaskSpider-style batch crawling with local mock server.

Uses LiteCrawler to avoid the Classic engine's task_spider loop complexity
while still testing the full fetch -> parse -> item collection pipeline.
"""

import typing

import pytest

from maize.aio.lite import LiteCrawler, LiteSpider
from maize.common.http import Request, Response
from maize.settings import SpiderSettings
from maize.utils.log_util import set_spider_settings


class MockTaskSpider(LiteSpider):
    """Spider that generates a fixed set of requests against the mock server."""

    def __init__(self):
        super().__init__()
        self.base_url: str = ""
        self._yielded = False

    async def start_requests(self) -> typing.AsyncGenerator[Request, typing.Any]:
        if self._yielded:
            return
        self._yielded = True

        yield Request(f"{self.base_url}/page/1")
        yield Request(f"{self.base_url}/page/2")
        yield Request(f"{self.base_url}/page/3")

    async def parse(self, response: Response):
        page_id = response.xpath("//span[@class='page-id']/text()").get()
        assert page_id is not None


@pytest.mark.asyncio
async def test_task_spider_with_mock_server(mock_server: str):
    """TaskSpider: start_requests yields requests, fetch + parse completes."""
    set_spider_settings(SpiderSettings())

    spider = MockTaskSpider()
    spider.base_url = mock_server
    await spider.open()

    crawler = LiteCrawler(spider, concurrency=1)
    await crawler.crawl()

    # All 3 requests should have been processed
    assert crawler.stats["succeeded"] == 3
