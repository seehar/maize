import logging
from collections.abc import Generator

import httpx

from maize.base.interface.sync_lite_spider_interface import SyncLiteSpiderInterface
from maize.common.http import Request, Response
from maize.common.items import Item
from maize.sync.lite.crawler.sync_lite_crawler import SyncLiteCrawler
from maize.utils.log_util import get_logger


class SyncLiteSpider(SyncLiteSpiderInterface):
    """
    同步 Lite 爬虫 - 轻量级同步爬虫，内置线程池并发、失败重试、代理支持。

    与异步 ``LiteSpider`` 相比，本类全部方法为同步（非 async），使用 ``httpx.Client``
    发起请求，``SyncLiteCrawler`` 用线程池实现并发。适合不希望使用 asyncio 的场景，
    或在同步代码库中快速集成爬虫功能。

    使用方式：继承此类，实现 ``start_requests`` 和 ``parse`` 方法（同步生成器）。

    :param concurrency: 最大并发数，默认 5
    :param retry: 最大请求尝试次数（含首次），默认 3。设为 0 则不发起任何请求
    :param proxy: 代理地址，默认 None
    :param timeout: 请求超时时间（秒），默认 30.0
    :param log_level: 日志级别，默认 "INFO"
    """

    def __init__(
        self,
        concurrency: int | None = None,
        retry: int | None = None,
        proxy: str | None = None,
        timeout: float | None = None,
        log_level: str | None = None,
    ):
        super().__init__()
        self._concurrency = concurrency
        self._retry = retry
        self._proxy = proxy
        self._timeout = timeout
        self._log_level = log_level

        self._client: httpx.Client | None = None
        self._logger: logging.Logger = logging.getLogger(f"maize.sync.lite.{self.__class__.__name__}")

    @property
    def concurrency(self) -> int:
        """最大并发数"""
        return self._concurrency if self._concurrency is not None else 5

    @property
    def retry(self) -> int:
        """最大请求尝试次数（含首次），0 表示不发起请求"""
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

        设为 False 时整个 spider 不做 URL 去重。
        单个请求仍可用 Request(meta={"dont_filter": True}) 跳过去重。
        """
        return True

    @property
    def per_domain_concurrency(self) -> int:
        """
        单域名最大并发数，0 表示不限（用全局 concurrency）。

        按请求 URL 的 netloc 分组限流。设为 1 即单域名串行抓取。
        """
        return 0

    @property
    def default_headers(self) -> dict[str, str]:
        """默认请求头，在 ``open()`` 时合入 Client。"""
        return {
            "User-Agent": "maize-sync-lite/1.0",
        }

    @property
    def log_level(self) -> str:
        """日志级别，默认 INFO"""
        return self._log_level if self._log_level is not None else "INFO"

    @property
    def logger(self) -> logging.Logger:
        """日志记录器"""
        return self._logger

    def open(self) -> None:
        """
        初始化资源。

        创建 httpx.Client，合入 ``default_headers``，初始化日志记录器。
        """
        self._logger = get_logger(
            name=f"maize.sync.lite.{self.__class__.__name__}",
            log_level=self.log_level,
        )
        self._client = httpx.Client(
            timeout=self.timeout,
            headers=self.default_headers,
        )

    def close(self) -> None:
        """关闭 httpx.Client。"""
        if self._client:
            self._client.close()
            self._client = None

    def on_start(self) -> None:
        """爬虫启动前调用，可在此处初始化数据库连接等资源"""

    def on_close(self) -> None:
        """爬虫关闭后调用，可在此处清理数据库连接等资源"""

    def should_retry(self, response: Response) -> bool:
        """
        判断响应是否需要重试。

        默认对 status==0（连接失败）、status>=500（服务端错误）、
        status==429（限流）重试。子类可重写以自定义重试策略。

        :param response: 响应对象
        :returns: True 表示需要重试
        """
        return response.status == 0 or response.status >= 500 or response.status == 429

    def process_item(self, item: Item) -> None:
        """
        处理采集到的数据项。

        在 parse 中 yield Item 后自动调用。子类可重写以实现数据落盘。
        默认空实现，Item 仍会保留在 crawler.items 中。

        :param item: 采集到的数据项
        """

    def start_requests(self) -> Generator[Request, None, None]:
        """
        生成起始请求。

        :returns: 生成器 yields Request 对象
        :raises NotImplementedError: 子类必须实现此方法
        """
        raise NotImplementedError

    def parse(self, response: Response):
        """
        解析响应。

        两种用法：
        1. 无需跟进链接：直接 return，与旧版行为一致
        2. 需要跟进链接或产出数据：yield Request（自动入队继续抓取）或 Item（自动收集）

        :param response: HTTP 响应对象
        :raises NotImplementedError: 子类必须实现此方法
        """
        raise NotImplementedError

    def fetch(self, request: Request) -> Response:
        """
        执行 HTTP 请求（同步）。

        使用 httpx.Client 发起请求，支持代理、超时等功能。
        请求失败时返回 status=0 的 Response 对象。

        :param request: 请求对象
        :returns: 响应对象
        """
        if not self._client:
            raise RuntimeError("Client not initialized. Did you call open()?")

        request_proxy = request.proxy or self.proxy

        try:
            headers = request.get_headers_sync()

            # httpx 不支持 per-request proxy/max_redirects，需创建临时 client
            need_temp_client = (request_proxy and request_proxy != self.proxy) or request.max_redirects != 20
            if need_temp_client:
                client = httpx.Client(
                    timeout=self.timeout,
                    headers=self.default_headers,
                    proxy=request_proxy,
                    max_redirects=request.max_redirects,
                )
                should_close = True
            else:
                client = self._client
                should_close = False

            try:
                response = client.request(
                    method=request.method,
                    url=request.url,
                    headers=headers,
                    data=request.data,  # type: ignore[arg-type]
                    json=request.json,
                    params=request.params,
                    cookies=request.cookies,  # type: ignore[arg-type]
                    follow_redirects=request.follow_redirects,
                )
                body = response.content
            finally:
                if should_close:
                    client.close()

            return Response(
                url=str(response.url),
                headers=dict(response.headers),
                status=response.status_code,
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
        快捷运行方法（同步，阻塞当前线程，支持优雅关闭）。

        Ctrl+C / SIGTERM 时，``SyncLiteCrawler`` 会停止接受新请求
        并等待 in-flight 请求完成后退出，保证 ``on_close`` 钩子被执行以清理资源。
        """
        try:
            crawler = SyncLiteCrawler(
                spider=self,
                concurrency=self.concurrency,
            )
            crawler.crawl()
        except KeyboardInterrupt:
            self.logger.info("收到中断信号，爬虫已停止")
