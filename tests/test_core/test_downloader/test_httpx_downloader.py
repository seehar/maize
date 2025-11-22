from collections.abc import AsyncGenerator
from typing import Any

import pytest

from maize import Request, Response, Spider, SpiderSettings
from maize.common.constant import SpiderDownloaderEnum


class HttpxProxySpider(Spider):
    async def start_requests(self) -> AsyncGenerator[Request, Any]:
        yield Request(url="https://dev.kdlapi.com/testproxy")

    async def parse(self, response: Response):
        self.logger.info(response.text)

    def start(self):
        settings = SpiderSettings()
        settings.downloader = SpiderDownloaderEnum.HTTPX.value
        self.run(settings)


@pytest.mark.asyncio
class TestHttpxDownloader:
    def test_run(self):
        HttpxProxySpider().start()
