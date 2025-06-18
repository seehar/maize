import pytest

from tests.test_full_process.test_spider.settings import BaiduSpiderSettings
from tests.test_full_process.test_spider.spiders.baidu_spider import BaiduSpider


@pytest.mark.asyncio
async def test_run():
    await BaiduSpider()._async_run(BaiduSpiderSettings())
