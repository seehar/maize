from collections.abc import AsyncGenerator
from typing import Any

from maize import Request, Response, Spider


class SpiderTemplate(Spider):
    async def start_requests(self) -> AsyncGenerator[Request, Any]:
        yield Request(url="url_template")

    async def parse(self, response: Response):
        self.logger.debug(response.text)
