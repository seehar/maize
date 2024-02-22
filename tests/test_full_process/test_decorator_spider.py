import pytest

from maize import Spider
from maize import SpiderEntry


spider_entry = SpiderEntry()


@spider_entry.register()
class BaiduSpider(Spider):
    start_url = "http://www.baidu.com"

    def parse(self, response):
        print(response.text)


def test_decorator_spider_list():
    assert len(spider_entry.get_spider_list()) == 1


def test_decorator_run():
    SpiderEntry().run()


@pytest.mark.asyncio
async def test_decorator_run_async():
    await SpiderEntry().run_async()
