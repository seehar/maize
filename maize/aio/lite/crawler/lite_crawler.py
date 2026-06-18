"""
Lite 爬虫运行器。

负责爬虫的启动、并发控制、请求调度和生命周期管理。
"""

import asyncio
import logging
import typing

from maize.common.http import Request, Response
from maize.common.items import Item


class LiteCrawler:
    """
    Lite 爬虫运行器。

    负责调度爬虫执行，管理并发和重试逻辑。
    使用队列 + 固定 Worker 的并发模型，支持：
    - 惰性拉取 start_requests（非预创建所有 Task）
    - 流式 parse：fetch 完成后立即处理
    - parse 中 yield Request 可递归跟进链接
    - parse 中 yield Item 自动收集

    :param spider: LiteSpider 实例
    :param concurrency: 最大并发数，默认使用 spider.concurrency
    """

    def __init__(self, spider: typing.Any, concurrency: int | None = None):
        self.spider = spider
        self.concurrency = concurrency if concurrency is not None else spider.concurrency
        self._items: list[Item] = []
        self._logger = logging.getLogger(f"maize.lite.crawler.{self.__class__.__name__}")

    @property
    def logger(self) -> logging.Logger:
        """日志记录器"""
        return self._logger

    @property
    def items(self) -> list[Item]:
        """parse 中 yield 出的 Item 列表"""
        return list(self._items)

    async def crawl(self) -> None:
        """
        运行爬虫主流程。

        1. 初始化 spider 资源（open）
        2. 调用 spider.on_start()
        3. 启动 start_requests 馈送任务
        4. 启动 concurrency 个 Worker，消费请求队列
        5. 监听 Worker 产出：Request 重新入队，Item 自动收集
        6. 所有请求处理完毕后清理资源
        """
        await self.spider.open()
        await self.spider.on_start()

        request_queue: asyncio.Queue[Request | None] = asyncio.Queue()
        start_requests_done = False

        async def feed_start_requests():
            nonlocal start_requests_done
            try:
                async for request in self.spider.start_requests():
                    await request_queue.put(request)
            finally:
                start_requests_done = True

        feed_task = asyncio.create_task(feed_start_requests())

        async def worker():
            while True:
                request = await request_queue.get()
                if request is None:
                    request_queue.task_done()
                    break
                await self._process(request, request_queue)

        workers = [asyncio.create_task(worker()) for _ in range(self.concurrency)]

        try:
            await feed_task
            await request_queue.join()
        finally:
            for _ in workers:
                await request_queue.put(None)
            await asyncio.gather(*workers)

            await self.spider.on_close()
            await self.spider.close()

    async def _process(self, request: Request, request_queue: asyncio.Queue) -> None:
        """处理单个请求：fetch + parse + 处理产出"""
        try:
            response = await self._fetch_with_retry(request)
        except Exception as e:
            self.logger.error(f"Unhandled fetch error for {request.url}: {e}")
            request_queue.task_done()
            return

        try:
            result = self.spider.parse(response)
            if hasattr(result, "__anext__"):
                async for output in result:
                    if isinstance(output, Request):
                        await request_queue.put(output)
                    elif isinstance(output, Item):
                        self._items.append(output)
            else:
                await result
        except Exception as e:
            self.logger.error(f"Parse error for {request.url}: {e}")
        finally:
            request_queue.task_done()

    async def _fetch_with_retry(self, request: Request) -> Response:
        """
        带重试的请求。

        重试条件：
        - status == 0（连接失败）
        - status >= 500（服务端错误）
        - status == 429（限流）
        每次重试前递增指数退避延迟（1s, 2s, 4s...）。

        :param request: 请求对象
        :returns: 最终的响应对象（成功或最后一次失败）
        """
        last_response: Response | None = None

        for attempt in range(self.spider.retry):
            response = await self.spider.fetch(request)
            last_response = response

            if not self._should_retry(response):
                return response

            if attempt < self.spider.retry - 1:
                request.retry()
                delay = 2**attempt
                self.logger.warning(
                    f"Retry {attempt + 1}/{self.spider.retry} for {request.url} "
                    f"(status={response.status}), waiting {delay}s"
                )
                await asyncio.sleep(delay)

        return last_response or Response(
            url=request.url,
            headers={},
            status=0,
            body=b"",
            request=request,
        )

    @staticmethod
    def _should_retry(response: Response) -> bool:
        """判断是否需要重试"""
        return response.status == 0 or response.status >= 500 or response.status == 429
