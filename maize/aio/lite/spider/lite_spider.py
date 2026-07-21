import asyncio
import logging
import typing
from collections.abc import AsyncGenerator

import aiohttp

from maize.aio.lite.crawler import LiteCrawler
from maize.base.interface.lite_spider_interface import LiteSpiderInterface
from maize.common.http import Request, Response
from maize.common.items import Item


class LiteSpider(LiteSpiderInterface):
    """
    Lite 爬虫 - 轻量级异步爬虫，内置并发控制、失败重试、代理支持。

    与 Classic 爬虫相比，Lite 版本更加轻量，适合简单抓取场景。
    使用方式：继承此类，实现 ``start_requests`` 和 ``parse`` 方法。

    :param concurrency: 最大并发数，默认 5
    :param retry: 请求失败重试次数，默认 3
    :param proxy: 代理地址，默认 None
    :param timeout: 请求超时时间（秒），默认 30.0
    """

    def __init__(
        self,
        concurrency: int | None = None,
        retry: int | None = None,
        proxy: str | None = None,
        timeout: float | None = None,
    ):
        super().__init__()
        self._concurrency = concurrency
        self._retry = retry
        self._proxy = proxy
        self._timeout = timeout

        self._session: aiohttp.ClientSession | None = None
        self._logger = logging.getLogger(f"maize.lite.{self.__class__.__name__}")

    @property
    def concurrency(self) -> int:
        """最大并发数"""
        return self._concurrency if self._concurrency is not None else 5

    @property
    def retry(self) -> int:
        """请求失败重试次数"""
        return self._retry if self._retry is not None else 3

    @property
    def proxy(self) -> str | None:
        """代理地址"""
        return self._proxy

    @property
    def timeout(self) -> float:
        """请求超时时间（秒）"""
        return self._timeout if self._timeout is not None else 30.0

    @property
    def max_depth(self) -> int:
        """
        最大爬取深度，0 表示不限。

        start_requests 产出的请求为 depth=0，parse 中 yield 的 Request
        每跟进一层 depth + 1。超过 max_depth 的请求会被丢弃。
        """
        return 0

    @property
    def dedup(self) -> bool:
        """
        是否启用请求去重，默认 True。

        设为 False 时整个 spider 不做 URL 去重，适合轮询采集、
        重复抓取同一 URL 监控变化等场景。
        单个请求仍可用 Request(meta={"dont_filter": True}) 跳过去重。
        """
        return True

    @property
    def default_headers(self) -> dict[str, str]:
        """
        默认请求头，在 ``open()`` 时合入 ClientSession。

        子类可重写以定制 UA、Accept 等请求头。per-request 的 ``Request.headers``
        仍优先于 session 级 headers。不引入中间件，保持 Lite 轻量。
        """
        return {
            "User-Agent": "maize-lite/1.0",
        }

    @property
    def logger(self) -> logging.Logger:
        """日志记录器"""
        return self._logger

    async def open(self) -> None:
        """
        初始化资源。

        创建 aiohttp ClientSession，合入 ``default_headers``，
        子类可重写 ``on_start`` 做额外初始化。
        """
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        self._session = aiohttp.ClientSession(
            timeout=timeout,
            headers=self.default_headers,
        )

    async def close(self) -> None:
        """
        清理资源。

        关闭 aiohttp ClientSession，子类可重写 ``on_close`` 做额外清理。
        """
        if self._session:
            await self._session.close()
            self._session = None

    async def on_start(self) -> None:
        """爬虫启动前调用，可在此处初始化数据库连接等资源"""

    async def on_close(self) -> None:
        """爬虫关闭后调用，可在此处清理数据库连接等资源"""

    async def process_item(self, item: Item) -> None:
        """
        处理采集到的数据项。

        在 parse 中 yield Item 后自动调用。子类可重写以实现数据落盘
        （写文件、写数据库等）。默认空实现，Item 仍会保留在 crawler.items 中。

        :param item: 采集到的数据项
        """

    async def start_requests(self) -> AsyncGenerator[Request, typing.Any]:
        """
        生成起始请求。

        :returns: 生成器 yields Request 对象
        :raises NotImplementedError: 子类必须实现此方法
        """
        raise NotImplementedError

    async def parse(self, response: Response):
        """
        解析响应。

        两种用法：
        1. 无需跟进链接：直接 return，与旧版行为一致
        2. 需要跟进链接或产出数据：yield Request（自动入队继续抓取）或 Item（自动收集）

        :param response: HTTP 响应对象
        :raises NotImplementedError: 子类必须实现此方法
        """
        raise NotImplementedError

    async def fetch(self, request: Request) -> Response:
        """
        执行 HTTP 请求。

        使用 aiohttp 发起请求，支持代理、重试、超时等功能。
        请求失败时返回 status=0 的 Response 对象。

        :param request: 请求对象
        :returns: 响应对象
        """
        if not self._session:
            raise RuntimeError("Session not initialized. Did you call open()?")

        request_proxy = request.proxy or self.proxy

        try:
            headers = await request.get_headers()
            async with self._session.request(
                method=request.method,
                url=request.url,
                headers=headers,
                data=request.data,
                json=request.json,
                params=request.params,
                cookies=request.cookies,
                proxy=request_proxy,
                allow_redirects=request.follow_redirects,
                max_redirects=request.max_redirects,
            ) as response:
                body = await response.read()
                return Response(
                    url=str(response.url),
                    headers=dict(response.headers.items()),
                    status=response.status,
                    body=body,
                    request=request,
                    source_response=response,
                )
        except Exception as e:
            self.logger.error(f"Request failed: {request.url}, error: {e}")
            return Response(
                url=request.url,
                headers={},
                status=0,
                body=b"",
                request=request,
            )

    def run(self) -> None:
        """
        快捷运行方法（支持优雅关闭）。

        同步入口，内部创建事件循环执行爬虫。Ctrl+C / SIGTERM 时，
        ``LiteCrawler`` 会停止接受新请求并等待 in-flight 请求完成后退出，
        保证 ``on_close`` 钩子被执行以清理资源。
        """
        try:
            asyncio.run(self._run())
        except KeyboardInterrupt:
            self.logger.info("收到中断信号，爬虫已停止")

    async def _run(self) -> None:
        """内部异步运行逻辑，创建 LiteCrawler 并执行爬虫流程"""
        crawler = LiteCrawler(
            spider=self,
            concurrency=self.concurrency,
        )
        await crawler.crawl()
