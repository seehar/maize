"""
中间件系统示例

本示例演示如何在 Maize 中使用中间件系统
展示内容:
1. 如何创建自定义中间件
2. 如何在配置中配置中间件
3. 不同类型的中间件（下载器、爬虫、管道）
"""

import asyncio
from collections.abc import AsyncGenerator
from typing import Any

from maize import Item, Request, Response, Spider
from maize.common.constant import LogLevelEnum
from maize.common.items.field import Field
from maize.core.crawler import CrawlerProcess
from maize.middlewares import (
    DownloaderMiddleware,
    PipelineMiddleware,
    SpiderMiddleware,
)
from maize.settings import MiddlewareSettings, SpiderSettings

# ============================================================================
# 自定义中间件
# ============================================================================


class CustomUserAgentMiddleware(DownloaderMiddleware):
    """为请求添加自定义 User-Agent 的中间件"""

    async def process_request(self, request: Request, spider: Spider) -> Request:
        """
        添加自定义 User-Agent 请求头

        :param request: 请求实例
        :param spider: 爬虫实例
        :return: 修改后的请求
        """
        if not request.headers:
            request.headers = {}
        request.headers["User-Agent"] = "MaizeBot/1.0 (Custom Middleware Example)"
        self.logger.info(f"Added custom User-Agent to request: {request.url}")
        return request


class RequestLoggingMiddleware(DownloaderMiddleware):
    """记录所有请求和响应的中间件"""

    async def open(self):
        pass

    async def close(self):
        pass

    async def process_request(self, request: Request, spider: Spider) -> Request:
        """
        记录请求信息

        :param request: 请求实例
        :param spider: 爬虫实例
        :return: 请求实例
        """
        self.logger.info(f"[REQUEST] {request.method} {request.url}")
        return request

    async def process_response(self, request: Request, response: Response, spider: Spider) -> Response:
        """
        记录响应信息

        :param request: 请求实例
        :param response: 响应实例
        :param spider: 爬虫实例
        :return: 响应实例
        """
        self.logger.info(f"[RESPONSE] {response.status} {request.url} (size: {len(response.body)} bytes)")
        return response


class DepthLimitMiddleware(SpiderMiddleware):
    """限制爬取深度的中间件"""

    def __init__(self, settings=None, max_depth=1):
        """
        初始化深度限制中间件

        :param settings: 爬虫配置
        :param max_depth: 最大深度
        """
        super().__init__(settings)
        self.max_depth = max_depth

    async def process_spider_output(self, response: Response, result: AsyncGenerator, spider: Spider) -> AsyncGenerator:
        """
        根据深度过滤请求

        :param response: 响应实例
        :param result: 结果生成器
        :param spider: 爬虫实例
        :return: 过滤后的结果
        """
        async for item in result:
            if item.__class__.__name__ == "Request":
                # 获取当前深度
                depth = item.meta.get("depth", 0) if item.meta else 0

                if depth >= self.max_depth:
                    self.logger.info(f"Dropping request {item.url} due to depth limit ({depth} >= {self.max_depth})")
                    continue

                # 为下一层增加深度
                if not item.meta:
                    item.meta = {}
                item.meta["depth"] = depth + 1

            yield item


class ItemCountMiddleware(PipelineMiddleware):
    """统计 Item 数量的中间件"""

    def __init__(self, settings=None):
        """
        初始化 Item 计数中间件

        :param settings: 爬虫配置
        """
        super().__init__(settings)
        self.item_count = 0

    async def process_item_before(self, item: Item, spider: Spider) -> Item:
        """
        在管道处理前统计 Item

        :param item: Item 实例
        :param spider: 爬虫实例
        :return: Item 实例
        """
        self.item_count += 1
        self.logger.info(f"Processing item #{self.item_count}: {item.__class__.__name__}")
        return item

    async def close(self):
        """
        关闭时记录统计信息
        """
        self.logger.info(f"Total items processed: {self.item_count}")


# ============================================================================
# 爬虫定义
# ============================================================================


class ExampleItem(Item):
    """演示用的示例 Item"""

    title: str = Field(description="页面标题")
    url: str = Field(description="页面 URL")


class MiddlewareExampleSpider(Spider):
    """演示中间件使用的示例爬虫"""

    # 配置自定义中间件
    custom_settings = SpiderSettings(
        middleware=MiddlewareSettings(
            downloader_middlewares={
                # 自定义中间件（优先级越高越晚执行）
                CustomUserAgentMiddleware: 100,
                RequestLoggingMiddleware: 200,
            },
            spider_middlewares={
                DepthLimitMiddleware: 100,
            },
            pipeline_middlewares={
                ItemCountMiddleware: 100,
            },
        ),
        log_level=LogLevelEnum.DEBUG.value,
    )

    async def start_requests(self) -> AsyncGenerator[Request, Any]:
        """
        生成初始请求

        :return: 请求生成器
        """
        urls = [
            "https://httpbin.org/html",
            "https://httpbin.org/json",
            "https://httpbin.org/user-agent",
        ]

        for url in urls:
            yield Request(url=url, callback=self.parse, meta={"depth": 0})

    async def parse(self, response: Response):
        """
        解析响应

        :param response: 响应实例
        """
        self.logger.info(f"Parsing: {response.url}")

        # 提取标题（简化版）
        title = "Example Page"

        # 生成 Item
        yield ExampleItem(title=title, url=response.url)

        # 生成后续请求（将被深度中间件过滤）
        if response.meta.get("depth", 0) < 2:
            yield Request(
                url="https://httpbin.org/delay/1",
                callback=self.parse,
                meta={"depth": response.meta.get("depth", 0) + 1},
            )


# ============================================================================
# 主执行函数
# ============================================================================


async def main():
    """
    运行带有中间件系统的爬虫
    """
    print("=" * 80)
    print("Maize 中间件系统示例")
    print("=" * 80)
    print()
    print("本示例演示:")
    print("1. 自定义 User-Agent 中间件")
    print("2. 请求/响应日志记录中间件")
    print("3. 深度限制中间件")
    print("4. Item 计数中间件")
    print()
    print("=" * 80)
    print()

    # 创建爬虫配置
    settings = SpiderSettings(
        project_name="中间件示例",
        concurrency=2,
        log_level="INFO",
    )

    # 创建并运行爬虫
    process = CrawlerProcess(settings=settings)
    await process.crawl(MiddlewareExampleSpider)
    await process.start()

    print()
    print("=" * 80)
    print("示例完成！")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
