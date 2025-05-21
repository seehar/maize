from typing import Any
from typing import AsyncGenerator

from maize import Request
from maize import Response
from maize import Spider


class SpiderTemplate(Spider):
    async def start_requests(self) -> AsyncGenerator[Request, Any]:
        yield Request(url="url_template")

    async def parse(self, response: Response):
        self.logger.debug(response.text)
