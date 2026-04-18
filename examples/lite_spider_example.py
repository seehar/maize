"""
Lite 爬虫示例

演示如何使用 Lite 版本的简单爬虫
"""

import asyncio
import logging
import typing

from maize.aio.lite import LiteSpider
from maize.common.http import Request, Response

# 配置 logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s - %(message)s",
)


class SimpleLiteSpider(LiteSpider):
    """简单的 Lite 爬虫示例"""

    async def start_requests(self) -> typing.AsyncGenerator[Request, typing.Any]:
        """生成初始请求"""
        urls = [
            "https://httpbin.org/get",
            "https://httpbin.org/json",
            "https://httpbin.org/html",
        ]
        for url in urls:
            yield Request(url=url)

    async def parse(self, response: Response):
        """解析响应"""
        self.logger.info(f"Status: {response.status}, URL: {response.url}")
        if response.status == 200:
            self.logger.info(f"Body preview: {response.text[:200] if response.text else 'No body'}")


async def main():
    """运行示例爬虫"""
    print("=" * 60)
    print("Lite Spider Example")
    print("=" * 60)

    spider = SimpleLiteSpider()
    await spider.crawl()

    print()
    print("Done!")


if __name__ == "__main__":
    asyncio.run(main())
