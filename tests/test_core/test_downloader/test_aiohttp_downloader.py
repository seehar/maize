import pytest

from maize import CrawlerProcess
from maize import Spider


class AioHttpProxySpider(Spider):
    start_url = "https://dev.kdlapi.com/testproxy"


@pytest.mark.asyncio
class TestAioHttpDownloader:
    async def test_run(self):
        process = CrawlerProcess()
        await process.crawl(AioHttpProxySpider)
        await process.start()
