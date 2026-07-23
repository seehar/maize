"""
同步 Classic 爬虫示例

演示如何使用同步版本的 Classic 爬虫，包含中间件、管道、调度器完整链路。
使用 httpx 同步下载器，线程池实现并发。
"""

import logging
from collections.abc import Generator
from typing import Any

from maize import Request, Response, SpiderSettings, SyncSpider, SyncSpiderDownloaderEnum
from maize.sync.classic.crawler.sync_crawler import SyncCrawlerProcess

# 配置 logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s - %(message)s",
)


class MySyncSpider(SyncSpider):
    """同步 Classic 爬虫示例"""

    def start_requests(self) -> Generator[Request, Any, None]:
        yield Request(url="https://httpbin.org/get")
        yield Request(url="https://httpbin.org/json")

    def parse(self, response: Response):
        self.logger.info(f"状态码: {response.status}")
        self.logger.info(f"URL: {response.url}")
        if response.status == 200:
            self.logger.info(f"内容预览: {response.text[:100]}...")


if __name__ == "__main__":
    print("=" * 60)
    print("Sync Classic Spider Example")
    print("=" * 60)

    settings = SpiderSettings(
        project_name="同步爬虫示例",
        concurrency=3,
        downloader=SyncSpiderDownloaderEnum.HTTPX.value,
    )

    process = SyncCrawlerProcess(settings=settings)
    process.crawl(MySyncSpider)
    process.start()

    print()
    print("Done!")
