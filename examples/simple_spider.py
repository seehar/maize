from collections.abc import AsyncGenerator
from typing import Any

from maize import Request, Response, Spider, SpiderSettings


class BaiduSpider(Spider):
    async def start_requests(self) -> AsyncGenerator[Request, Any]:
        yield Request(url="http://www.baidu.com")

    def parse(self, response: Response):
        self.logger.info(f"响应状态码: {response.status}")
        self.logger.info(f"响应内容: {response.text[:100]}...")


if __name__ == "__main__":
    settings = SpiderSettings(
        project_name="百度爬虫",
    )

    BaiduSpider().run(settings)
