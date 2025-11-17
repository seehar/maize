from typing import Any
from typing import AsyncGenerator

import pytest

from maize import Request
from maize import Response
from maize import Spider
from maize import SpiderSettings
from maize.common.constant import SpiderDownloaderEnum


class AioHttpProxySpider(Spider):
    async def start_requests(self) -> AsyncGenerator[Request, Any]:
        yield Request("https://dev.kdlapi.com/testproxy")

    async def parse(self, response: Response):
        self.logger.info(response.text)

    def start(self):
        settings = SpiderSettings()
        settings.downloader = SpiderDownloaderEnum.AIOHTTP.value
        self.run(settings)


@pytest.mark.asyncio
class TestAioHttpDownloader:
    def test_run(self):
        AioHttpProxySpider().start()
