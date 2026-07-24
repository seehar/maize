"""
Spider 代码模板。
"""

from collections.abc import AsyncGenerator
from typing import Any

from maize import Request, Response, Spider


class SpiderTemplate(Spider):
    """
    Spider 模板类，提供基础的 start_requests 和 parse 实现。
    """

    async def start_requests(self) -> AsyncGenerator[Request, Any]:
        yield Request(url="url_template")

    async def parse(self, response: Response):
        self.logger.debug(response.text)
