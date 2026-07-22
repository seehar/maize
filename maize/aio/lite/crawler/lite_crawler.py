"""
Lite 爬虫运行器。

负责爬虫的启动、并发控制、请求调度和生命周期管理。
"""

import asyncio
import contextlib
import logging
import signal
import time
import typing
from urllib.parse import urlparse

from maize.common.http import Request, Response
from maize.common.items import Item


class LiteCrawler:
    """
    Lite 爬虫运行器。

    负责调度爬虫执行，管理并发和重试逻辑。
    使用优先级队列 + 固定 Worker 的并发模型，支持：
    - 惰性拉取 start_requests（非预创建所有 Task）
    - 流式 parse：fetch 完成后立即处理
    - parse 中 yield Request 可递归跟进链接（按 priority 出队）
    - parse 中 yield Item 自动收集
    - 请求去重与深度控制
    - 运行时统计（requested/succeeded/failed/retried/dropped/items）
    - 优雅关闭（SIGINT/SIGTERM 后等待 in-flight 请求完成再退出）

    :param spider: LiteSpider 实例
    :param concurrency: 最大并发数，默认使用 spider.concurrency
    """

    def __init__(self, spider: typing.Any, concurrency: int | None = None):
        self.spider = spider
        self.concurrency = concurrency if concurrency is not None else spider.concurrency
        self._items: list[Item] = []
        self._seen: set[str] = set()
        self._tie_breaker: int = 0
        self._stats: dict[str, int] = {
            "requested": 0,
            "succeeded": 0,
            "failed": 0,
            "retried": 0,
            "dropped": 0,
            "items": 0,
        }
        self._domain_semaphores: dict[str, asyncio.Semaphore] = {}
        self._logger = logging.getLogger(f"maize.lite.crawler.{self.__class__.__name__}")

    @property
    def logger(self) -> logging.Logger:
        """日志记录器"""
        return self._logger

    @property
    def items(self) -> list[Item]:
        """parse 中 yield 出的 Item 列表"""
        return list(self._items)

    @property
    def stats(self) -> dict[str, int]:
        """运行时统计：requested/succeeded/failed/retried/dropped/items"""
        return dict(self._stats)

    async def _enqueue(self, request: Request, request_queue: asyncio.PriorityQueue) -> bool:
        """
        入队前的过滤：深度控制 + 去重，通过则按 priority 入队。

        :returns: True 表示已入队，False 表示被丢弃
        """
        # 深度初始化：start_requests 产出的请求默认 depth=0
        if "_lite_depth" not in request.meta:
            request.meta["_lite_depth"] = 0

        depth = request.meta["_lite_depth"]
        max_depth = self.spider.max_depth
        if max_depth > 0 and depth > max_depth:
            self.logger.debug(f"Drop request (depth={depth} > max_depth={max_depth}): {request.url}")
            self._stats["dropped"] += 1
            return False

        # 去重：spider.dedup 全局开关 + dont_filter 单请求逃生口
        if self.spider.dedup and not request.meta.get("dont_filter", False):
            req_hash = request.hash
            if req_hash in self._seen:
                self.logger.debug(f"Drop duplicate request: {request.url}")
                self._stats["dropped"] += 1
                return False
            self._seen.add(req_hash)

        # PriorityQueue 需要可比较的 tuple；tie_breaker 保证同 priority 时按入队顺序出队，
        # 避免 Request.__lt__ 只比 priority 导致 tuple 第二项比较报错
        self._tie_breaker += 1
        await request_queue.put((float(request.priority), self._tie_breaker, request))
        self._stats["requested"] += 1
        return True

    async def crawl(self) -> None:
        """
        运行爬虫主流程。

        1. 初始化 spider 资源（open）
        2. 调用 spider.on_start()
        3. 启动 start_requests 馈送任务
        4. 启动 concurrency 个 Worker，消费优先级队列
        5. 监听 Worker 产出：Request 重新入队，Item 自动收集
        6. 所有请求处理完毕后清理资源，输出统计汇总
        7. 收到 SIGINT/SIGTERM 时停止接受新请求，等待 in-flight 完成后退出
        """
        await self.spider.open()
        await self.spider.on_start()

        stop_event = asyncio.Event()
        loop = asyncio.get_running_loop()

        def _signal_handler():
            if not stop_event.is_set():
                self.logger.info("收到停止信号，等待当前请求处理完毕后退出...")
                stop_event.set()

        signal_handlers_registered: list[signal.Signals] = []
        for sig in (signal.SIGINT, signal.SIGTERM):
            with contextlib.suppress(NotImplementedError, RuntimeError):
                # Windows 不支持 add_signal_handler，降级走 KeyboardInterrupt 兜底
                loop.add_signal_handler(sig, _signal_handler)
                signal_handlers_registered.append(sig)

        # PriorityQueue 按 priority 出队；哨兵用 (inf, inf, None) 保证最后出队
        request_queue: asyncio.PriorityQueue[tuple[float, int, Request | None]] = asyncio.PriorityQueue()

        async def feed_start_requests():
            try:
                async for request in self.spider.start_requests():
                    if stop_event.is_set():
                        break
                    await self._enqueue(request, request_queue)
            except Exception as e:
                self.logger.error(f"start_requests error: {e}")

        feed_task = asyncio.create_task(feed_start_requests())

        async def worker():
            while True:
                if stop_event.is_set():
                    # 停止接受新请求， drain 当前 in-flight 后退出
                    break
                try:
                    _priority, _seq, request = await asyncio.wait_for(request_queue.get(), timeout=0.5)
                except asyncio.TimeoutError:
                    continue
                if request is None:
                    request_queue.task_done()
                    break
                try:
                    await self._process(request, request_queue)
                except Exception as e:
                    self.logger.error(f"worker error: {e}")

        workers = [asyncio.create_task(worker()) for _ in range(self.concurrency)]

        try:
            await feed_task
            for _ in workers:
                self._tie_breaker += 1
                await request_queue.put((float("inf"), self._tie_breaker, None))
            await asyncio.gather(*workers, return_exceptions=True)
        finally:
            for sig in signal_handlers_registered:
                with contextlib.suppress(NotImplementedError, RuntimeError):
                    loop.remove_signal_handler(sig)

            await self.spider.on_close()
            await self.spider.close()
            self._log_stats()

    def _log_stats(self) -> None:
        """输出运行时统计汇总"""
        s = self._stats
        self.logger.info(
            f"Stats: requested={s['requested']}, succeeded={s['succeeded']}, "
            f"failed={s['failed']}, retried={s['retried']}, "
            f"dropped={s['dropped']}, items={s['items']}"
        )

    def _get_domain_semaphore(self, url: str) -> asyncio.Semaphore | None:
        """按 URL 的 netloc 获取或创建 domain semaphore，返回 None 表示不限流"""
        limit = self.spider.per_domain_concurrency
        if limit <= 0:
            return None
        netloc = urlparse(url).netloc or "unknown"
        if netloc not in self._domain_semaphores:
            self._domain_semaphores[netloc] = asyncio.Semaphore(limit)
        return self._domain_semaphores[netloc]

    async def _process(self, request: Request, request_queue: asyncio.PriorityQueue) -> None:
        """处理单个请求：fetch + parse + 处理产出"""
        parent_depth = request.meta.get("_lite_depth", 0)
        start_time = time.monotonic()
        sem = self._get_domain_semaphore(request.url)

        async def _do_fetch() -> Response:
            if sem:
                async with sem:
                    return await self._fetch_with_retry(request)
            return await self._fetch_with_retry(request)

        try:
            response = await _do_fetch()
        except Exception as e:
            elapsed = time.monotonic() - start_time
            self.logger.error(
                f"fetch_failed url={request.url} elapsed={elapsed:.2f}s retry={request.current_retry_count} error={e}"
            )
            self._stats["failed"] += 1
            request_queue.task_done()
            return

        elapsed = time.monotonic() - start_time
        self.logger.info(
            f"request url={request.url} status={response.status} "
            f"elapsed={elapsed:.2f}s retry={request.current_retry_count}"
        )

        # 统计成功/失败（status==0 视为连接失败）
        if 0 < response.status < 400:
            self._stats["succeeded"] += 1
        else:
            self._stats["failed"] += 1

        callback = request.callback or self.spider.parse

        try:
            result = callback(response)
            if hasattr(result, "__anext__"):
                async for output in result:
                    if isinstance(output, Request):
                        output.meta["_lite_depth"] = parent_depth + 1
                        await self._enqueue(output, request_queue)
                    elif isinstance(output, Item):
                        self._items.append(output)
                        self._stats["items"] += 1
                        try:
                            await self.spider.process_item(output)
                        except Exception as e:
                            self.logger.error(f"process_item_failed url={request.url} error={e}")
            else:
                await result
        except Exception as e:
            self.logger.error(
                f"parse_failed url={request.url} status={response.status} elapsed={elapsed:.2f}s error={e}"
            )
        finally:
            request_queue.task_done()

    async def _fetch_with_retry(self, request: Request) -> Response:
        """
        带重试的请求。

        重试条件由 ``spider.should_retry`` 决定（默认：status==0 / >=500 / 429）。
        每次重试前递增指数退避延迟（1s, 2s, 4s...）。

        :param request: 请求对象
        :returns: 最终的响应对象（成功或最后一次失败）
        """
        last_response: Response | None = None

        for attempt in range(self.spider.retry):
            response = await self.spider.fetch(request)
            last_response = response

            if not self.spider.should_retry(response):
                return response

            if attempt < self.spider.retry - 1:
                request.retry()
                self._stats["retried"] += 1
                delay = 2**attempt
                self.logger.warning(
                    f"retry url={request.url} attempt={attempt + 1}/{self.spider.retry} "
                    f"status={response.status} delay={delay}s"
                )
                await asyncio.sleep(delay)

        return last_response or Response(
            url=request.url,
            headers={},
            status=0,
            body=b"",
            request=request,
        )
