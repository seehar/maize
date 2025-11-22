from collections.abc import AsyncGenerator
from typing import Any

import pytest

from maize import Request, Spider, SpiderEntry

spider_entry = SpiderEntry()


@spider_entry.register()
class BaiduSpider(Spider):
    async def start_requests(self) -> AsyncGenerator[Request, Any]:
        yield Request("http://www.baidu.com")

    def parse(self, response):
        print(response.text)


def test_decorator_spider_list():
    assert len(spider_entry.get_spider_list()) == 1


def test_decorator_run():
    SpiderEntry().run()


@pytest.mark.asyncio
async def test_decorator_run_async():
    await SpiderEntry().run_async()
