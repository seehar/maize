"""
同步 Lite 爬虫运行器。

与异步版 ``LiteCrawler`` 对应，使用线程池实现并发。
复用 ``Request``/``Response``/``Item`` 等共享模型，不引入中间件/管道/调度器抽象。
"""

import contextlib
import logging
import queue
import signal
import threading
import time
import typing
from urllib.parse import urlparse

from maize.common.http import Request, Response
from maize.common.items import Item


class SyncLiteCrawler:
    """
    同步 Lite 爬虫运行器。

    负责调度爬虫执行，管理线程池并发和重试逻辑。
    使用优先级队列 + 固定 Worker 的并发模型，支持：
    - 惰性拉取 start_requests
    - 流式 parse：fetch 完成后立即处理
    - parse 中 yield Request 可递归跟进链接
    - parse 中 yield Item 自动收集
    - 请求去重与深度控制
    - 运行时统计
    - 优雅关闭（SIGINT/SIGTERM 后等待 in-flight 请求完成再退出）

    :param spider: SyncLiteSpider 实例
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
        self._domain_semaphores: dict[str, threading.Semaphore] = {}
        self._logger = spider.logger
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

    @property
    def logger(self) -> logging.Logger:
        """日志记录器（复用 spider 的 logger）"""
        return self._logger  # type: ignore[no-any-return]

    @property
    def items(self) -> list[Item]:
        """parse 中 yield 出的 Item 列表"""
        return list(self._items)

    @property
    def stats(self) -> dict[str, int]:
        """运行时统计：requested/succeeded/failed/retried/dropped/items"""
        return dict(self._stats)

    def _enqueue(self, request: Request, request_queue: queue.PriorityQueue) -> bool:
        """
        入队前的过滤：深度控制 + 去重，通过则按 priority 入队。

        :returns: True 表示已入队，False 表示被丢弃
        """
        if "_lite_depth" not in request.meta:
            request.meta["_lite_depth"] = 0

        depth = request.meta["_lite_depth"]
        max_depth = self.spider.max_depth
        if max_depth > 0 and depth > max_depth:
            self.logger.debug(f"Drop request (depth={depth} > max_depth={max_depth}): {request.url}")
            with self._lock:
                self._stats["dropped"] += 1
            return False

        if self.spider.dedup and not request.meta.get("dont_filter", False):
            req_hash = request.hash
            with self._lock:
                if req_hash in self._seen:
                    self.logger.debug(f"Drop duplicate request: {request.url}")
                    self._stats["dropped"] += 1
                    return False
                self._seen.add(req_hash)

        with self._lock:
            self._tie_breaker += 1
            request_queue.put((float(request.priority), self._tie_breaker, request))
            self._stats["requested"] += 1
        return True

    def crawl(self) -> None:
        """
        运行爬虫主流程（同步，阻塞当前线程）。

        1. 初始化 spider 资源（open）
        2. 调用 spider.on_start()
        3. 启动 start_requests 馈送线程
        4. 启动 concurrency 个 Worker 线程，消费优先级队列
        5. 所有请求处理完毕后清理资源，输出统计汇总
        """
        self._stop_event.clear()
        self.spider.open()

        # 信号处理（仅主线程有效）
        def _signal_handler(_signum, _frame):
            if not self._stop_event.is_set():
                self.logger.info("收到停止信号，等待当前请求处理完毕后退出...")
                self._stop_event.set()

        signal_handlers_registered: list[signal.Signals] = []
        previous_handlers: dict[signal.Signals, typing.Any] = {}
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                previous_handlers[sig] = signal.getsignal(sig)
                signal.signal(sig, _signal_handler)
                signal_handlers_registered.append(sig)
            except (ValueError, OSError):
                # 非主线程无法注册信号处理器
                pass

        try:
            self.spider.on_start()

            request_queue: queue.PriorityQueue[tuple[float, int, Request | None]] = queue.PriorityQueue()
            feed_done = threading.Event()

            def feed_start_requests():
                try:
                    for request in self.spider.start_requests():
                        if self._stop_event.is_set():
                            break
                        self._enqueue(request, request_queue)
                except Exception as e:
                    self.logger.error(f"start_requests error: {e}")
                finally:
                    feed_done.set()

            def worker():
                while True:
                    if self._stop_event.is_set():
                        break
                    try:
                        _priority, _seq, request = request_queue.get(timeout=0.5)
                    except queue.Empty:
                        if feed_done.is_set() and request_queue.empty():
                            break
                        continue
                    if request is None:
                        request_queue.task_done()
                        break
                    try:
                        self._process(request, request_queue)
                    except Exception as e:
                        self.logger.error(f"worker error: {e}")

            feed_thread = threading.Thread(target=feed_start_requests, daemon=True)
            feed_thread.start()

            workers = [threading.Thread(target=worker, daemon=True) for _ in range(self.concurrency)]
            for w in workers:
                w.start()

            # 等待 feed 完成
            feed_thread.join()

            # 推入哨兵
            for _ in workers:
                with self._lock:
                    self._tie_breaker += 1
                    request_queue.put((float("inf"), self._tie_breaker, None))

            for w in workers:
                w.join()
        finally:
            # 恢复之前的信号处理器，避免嵌入式场景中 handler 残留
            for sig in signal_handlers_registered:
                with contextlib.suppress(Exception):
                    signal.signal(sig, previous_handlers[sig])

            try:
                self.spider.on_close()
            except Exception as e:
                self.logger.error(f"on_close error: {e}")

            try:
                self.spider.close()
            except Exception as e:
                self.logger.error(f"close error: {e}")

            self._log_stats()

    def _log_stats(self) -> None:
        """输出运行时统计汇总"""
        s = self._stats
        self.logger.info(
            f"Stats: requested={s['requested']}, succeeded={s['succeeded']}, "
            f"failed={s['failed']}, retried={s['retried']}, "
            f"dropped={s['dropped']}, items={s['items']}"
        )

    def _get_domain_semaphore(self, url: str) -> threading.Semaphore | None:
        """按 URL 的 netloc 获取或创建 domain semaphore，返回 None 表示不限流"""
        limit = self.spider.per_domain_concurrency
        if limit <= 0:
            return None
        netloc = urlparse(url).netloc or "unknown"
        with self._lock:
            if netloc not in self._domain_semaphores:
                self._domain_semaphores[netloc] = threading.Semaphore(limit)
        return self._domain_semaphores[netloc]

    def _process(self, request: Request, request_queue: queue.PriorityQueue) -> None:
        """处理单个请求：fetch + parse + 处理产出"""
        parent_depth = request.meta.get("_lite_depth", 0)
        start_time = time.monotonic()
        sem = self._get_domain_semaphore(request.url)

        def _do_fetch() -> Response:
            if sem:
                with sem:
                    return self._fetch_with_retry(request)
            return self._fetch_with_retry(request)

        try:
            response = _do_fetch()
        except Exception as e:
            elapsed = time.monotonic() - start_time
            self.logger.error(
                f"fetch_failed url={request.url} elapsed={elapsed:.2f}s retry={request.current_retry_count} error={e}"
            )
            with self._lock:
                self._stats["failed"] += 1
            request_queue.task_done()
            return

        elapsed = time.monotonic() - start_time
        self.logger.info(
            f"request url={request.url} status={response.status} "
            f"elapsed={elapsed:.2f}s retry={request.current_retry_count}"
        )

        if 0 < response.status < 400:
            with self._lock:
                self._stats["succeeded"] += 1
        else:
            with self._lock:
                self._stats["failed"] += 1

        callback = request.callback or self.spider.parse

        try:
            result = callback(response)
            if result is not None:
                for output in result:
                    if isinstance(output, Request):
                        output.meta["_lite_depth"] = parent_depth + 1
                        self._enqueue(output, request_queue)
                    elif isinstance(output, Item):
                        with self._lock:
                            self._items.append(output)
                            self._stats["items"] += 1
                        try:
                            self.spider.process_item(output)
                        except Exception as e:
                            self.logger.error(f"process_item_failed url={request.url} error={e}")
        except Exception as e:
            self.logger.error(
                f"parse_failed url={request.url} status={response.status} elapsed={elapsed:.2f}s error={e}"
            )
        finally:
            request_queue.task_done()

    def _fetch_with_retry(self, request: Request) -> Response:
        """
        带重试的请求。

        重试条件由 ``spider.should_retry`` 决定（默认：status==0 / >=500 / 429）。
        每次重试前递增指数退避延迟（1s, 2s, 4s...），``time.sleep`` 阻塞当前 worker 线程，
        收到停止信号时需等待 sleep 结束才能退出。

        :param request: 请求对象
        :returns: 最终的响应对象
        """
        last_response: Response | None = None

        for attempt in range(self.spider.retry):
            response = self.spider.fetch(request)
            last_response = response

            if not self.spider.should_retry(response):
                return response  # type: ignore[no-any-return]

            if attempt < self.spider.retry - 1:
                request.retry()
                with self._lock:
                    self._stats["retried"] += 1
                delay = 2**attempt
                self.logger.warning(
                    f"retry url={request.url} attempt={attempt + 1}/{self.spider.retry} "
                    f"status={response.status} delay={delay}s"
                )
                time.sleep(delay)

        if last_response is not None:
            return last_response
        return Response(
            url=request.url,
            headers={},
            status=0,
            body=b"",
            request=request,
        )
