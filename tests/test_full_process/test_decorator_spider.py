"""
Integration test: SpiderEntry decorator with local mock server.
"""

from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from maize import Request, Response, Spider, SpiderEntry
from maize.common.constant.setting_constant import SpiderDownloaderEnum
from maize.settings import SpiderSettings
from maize.utils.log_util import set_spider_settings


class DecoratorSpider(Spider):
    """Spider that crawls the mock server via SpiderEntry decorator."""

    def __init__(self):
        super().__init__()
        self.base_url: str = ""

    async def start_requests(self) -> AsyncGenerator[Request, Any]:
        yield Request(f"{self.base_url}/")

    def parse(self, response: Response):
        assert response.status == 200
        assert "Mock Search Engine" in response.text


@pytest.mark.asyncio
async def test_decorator_spider_register(mock_server: str):
    """SpiderEntry.register adds spider to the list."""
    entry = SpiderEntry()

    @entry.register()
    class MySpider(DecoratorSpider):
        pass

    assert len(entry.get_spider_list()) == 1


@pytest.mark.asyncio
async def test_decorator_spider_run_async(mock_server: str):
    """SpiderEntry.run_async runs the spider against the mock server."""
    set_spider_settings(SpiderSettings())

    settings = SpiderSettings()
    settings.concurrency = 1
    settings.downloader = SpiderDownloaderEnum.AIOHTTP.value
    settings.request.use_session = True
    settings.request.request_timeout = 10

    entry = SpiderEntry()

    @entry.register(settings={"downloader": SpiderDownloaderEnum.AIOHTTP.value})
    class MySpider(DecoratorSpider):
        def __init__(self):
            super().__init__()
            self.base_url = mock_server

    # Patch CrawlerProcess to verify spider registration
    with patch("maize.core.decorator_entry.CrawlerProcess") as mock_proc_cls:
        mock_proc = mock_proc_cls.return_value
        mock_proc.crawl = AsyncMock()
        mock_proc.start = AsyncMock()

        await entry.run_async()
        mock_proc_cls.assert_called_once()
        mock_proc.crawl.assert_called_once()
        mock_proc.start.assert_called_once()
