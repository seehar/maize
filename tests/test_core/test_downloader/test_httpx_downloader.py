import pytest

from maize import CrawlerProcess
from maize import Spider


class HttpxProxySpider(Spider):
    start_url = "https://dev.kdlapi.com/testproxy"

    custom_settings = {"DOWNLOADER": "maize.AioHttpDownloader"}


@pytest.mark.asyncio
class TestHttpxDownloader:
    async def test_run(self):
        process = CrawlerProcess()
        await process.crawl(HttpxProxySpider)
        await process.start()
