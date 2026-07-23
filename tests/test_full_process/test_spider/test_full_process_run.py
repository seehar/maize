"""
Integration test: full spider pipeline using a local mock server.

Tests the Classic spider pipeline:
  start_requests -> AioHttpDownloader -> parse -> pipeline -> item collection
"""

from collections.abc import AsyncGenerator
from typing import Any

import pytest

from maize import Item, Request, Response, Spider
from maize.aio.classic.crawler.crawler import CrawlerProcess
from maize.common.constant.setting_constant import SpiderDownloaderEnum
from maize.settings import SpiderSettings
from maize.utils.log_util import set_spider_settings


class MockItem(Item):
    __table_name__: str = "mock_pages"
    title: str = ""
    url: str = ""


class FullProcessSpider(Spider):
    """Spider that crawls the mock server, follows links, and yields items."""

    def __init__(self):
        super().__init__()
        self.base_url: str = ""

    async def start_requests(self) -> AsyncGenerator[Request, Any]:
        yield Request(f"{self.base_url}/")

    async def parse(self, response: Response):
        li_list = response.xpath("//li[contains(@class,'hotsearch-item')]")
        for li in li_list:
            title = li.xpath(".//span[@class='title-content-title']/text()").get()
            href = li.xpath("./a/@href").get()
            yield Request(url=f"{self.base_url}{href}", callback=self.parse_page)
            yield MockItem(title=title or "", url=f"{self.base_url}{href}")

    @staticmethod
    async def parse_page(response: Response):
        page_id = response.xpath("//span[@class='page-id']/text()").get()
        yield MockItem(title=f"Page {page_id}", url=response.url)


@pytest.mark.asyncio
async def test_full_process_with_mock_server(mock_server: str):
    """Full spider pipeline: download -> parse -> follow links -> collect items."""
    set_spider_settings(SpiderSettings())

    settings = SpiderSettings()
    settings.concurrency = 1
    settings.downloader = SpiderDownloaderEnum.AIOHTTP.value
    settings.request.use_session = True
    settings.request.request_timeout = 10

    spider = FullProcessSpider()
    spider.base_url = mock_server

    # Run the spider through CrawlerProcess
    process = CrawlerProcess(settings=settings, settings_path=None)
    await process.crawl(spider)
    await process.start()


@pytest.mark.asyncio
async def test_full_process_httpx_downloader(mock_server: str):
    """Full spider pipeline with HTTPX downloader."""
    set_spider_settings(SpiderSettings())

    settings = SpiderSettings()
    settings.concurrency = 1
    settings.downloader = SpiderDownloaderEnum.HTTPX.value
    settings.request.use_session = True
    settings.request.request_timeout = 10

    spider = FullProcessSpider()
    spider.base_url = mock_server

    process = CrawlerProcess(settings=settings, settings_path=None)
    await process.crawl(spider)
    await process.start()
