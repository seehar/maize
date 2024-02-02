import pytest

from maize import CrawlerProcess
from maize.utils import get_settings
from tests.test_full_process.test_spider.spiders.baidu_spider import BaiduSpider


@pytest.mark.asyncio
async def test_run():
    settings = get_settings(
        "tests.test_full_process.test_spider.settings.SpiderSettings"
    )
    process = CrawlerProcess(settings)
    await process.crawl(BaiduSpider)
    await process.start()
