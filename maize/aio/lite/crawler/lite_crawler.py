"""
Lite 爬虫运行器。

负责爬虫的启动、并发控制、请求调度和生命周期管理。
"""

import asyncio
import logging
import typing

from maize.common.http import Request, Response


class LiteCrawler:
    """
    Lite 爬虫运行器。

    负责调度爬虫执行，管理并发和重试逻辑。
    通常由 LiteSpider._run() 创建并执行。

    :param spider: LiteSpider 实例
    :param concurrency: 最大并发数，默认使用 spider.concurrency
    """

    def __init__(self, spider: typing.Any, concurrency: int | None = None):
        self.spider = spider
        self.concurrency = concurrency if concurrency is not None else spider.concurrency
        self._logger = logging.getLogger(f"maize.lite.crawler.{self.__class__.__name__}")

    @property
    def logger(self) -> logging.Logger:
        """日志记录器"""
        return self._logger

    async def crawl(self) -> None:
        """
        运行爬虫主流程。

        1. 初始化 spider 资源（open）
        2. 调用 spider.on_start()
        3. 并发执行所有请求
        4. 调用 spider.parse() 处理每个响应
        5. 调用 spider.on_close() 和 spider.close() 清理资源
        """
        await self.spider.open()
        await self.spider.on_start()

        semaphore = asyncio.Semaphore(self.concurrency)

        async def fetch_with_semaphore(request: Request) -> Response:
            async with semaphore:
                return await self._fetch_with_retry(request)

        try:
            tasks: list[asyncio.Task] = []
            # Mypy bug: abstract async generator return type causes false positive
            # Subclasses implement with `async def start_requests(self): yield request`
            async for request in self.spider.start_requests():
                task = asyncio.create_task(fetch_with_semaphore(request))
                tasks.append(task)

            for task in tasks:
                response = await task
                await self.spider.parse(response)
        finally:
            await self.spider.on_close()
            await self.spider.close()

    async def _fetch_with_retry(self, request: Request) -> Response:
        """
        带重试的请求。

        失败判定标准：response.status == 0
        每次重试前会调用 request.retry() 记录重试次数。

        :param request: 请求对象
        :returns: 最终的响应对象（成功或最后一次失败）
        """
        last_response: Response | None = None

        for _ in range(self.spider.retry):
            response = await self.spider.fetch(request)
            last_response = response

            if response.status != 0:
                break

            request.retry()

        return last_response or Response(
            url=request.url,
            headers={},
            status=0,
            body=b"",
            request=request,
        )
