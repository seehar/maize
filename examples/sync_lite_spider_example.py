"""
同步 Lite 爬虫示例

演示如何使用同步版本的轻量级爬虫，使用 httpx 同步模式 + 线程池并发。
"""

import logging
import typing

from maize.common.http import Request, Response
from maize.sync.lite import SyncLiteSpider

# 配置 logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s - %(message)s",
)


class SimpleSyncLiteSpider(SyncLiteSpider):
    """简单的同步 Lite 爬虫示例"""

    def start_requests(self) -> typing.Generator[Request, None, None]:
        """生成初始请求"""
        urls = [
            "https://httpbin.org/get",
            "https://httpbin.org/json",
            "https://httpbin.org/html",
        ]
        for url in urls:
            yield Request(url=url)

    def parse(self, response: Response):
        """解析响应"""
        self.logger.info(f"Status: {response.status}, URL: {response.url}")
        if response.status == 200:
            self.logger.info(f"Body preview: {response.text[:200] if response.text else 'No body'}")


if __name__ == "__main__":
    print("=" * 60)
    print("Sync Lite Spider Example")
    print("=" * 60)

    spider = SimpleSyncLiteSpider()
    spider.run()

    print()
    print("Done!")
