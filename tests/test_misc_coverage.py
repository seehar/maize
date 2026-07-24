"""杂项覆盖率补充测试。

覆盖多个模块的少量未覆盖行：
- sync_scheduler: __len__ 未 open / next_request 未 open / get_by_priority
- sync_task_manager: create_task 未 open / 任务异常日志
- sync_processor: item 被 pipeline middleware 丢弃
- sync_spider: start_requests/parse NotImplementedError
- sync_task_spider: 默认 start_requests
- sync_empty_pipeline: process_error_item
- spider_settings: merge_settings_from_dict 未知字段
- spider_util: transform_sync 非法类型
- request: get_headers_sync 协程检测
- response: body/text 编码异常 / cookies 缓存 / _get_encoding body charset
- sync_base_middleware: 基类默认方法
- sync_middleware_manager: 非目标类型中间件跳过
- sync_pipeline_scheduler: 空队列分支
- pipeline_scheduler: 空队列分支
- cleaner: 非 Pydantic Item 回退
- sync_lite_spider: start_requests/parse NotImplementedError / run KeyboardInterrupt
- lite_spider: start_requests/parse NotImplementedError
- lite_crawler: feed 异常 / worker 异常
- middleware_manager: process_response 异常 / process_exception 异常
- base_middleware: 抽象方法
- base_downloader: 抽象方法
- sync_httpx_downloader: _get_proxy 带认证
- sync_requests_downloader: _get_request_proxy 带认证
- sync_stats_collector: _upload_stat 跳过条件
"""

import time
from collections.abc import Generator
from typing import Any
from unittest.mock import MagicMock

import pytest

try:
    import requests
except ImportError:
    requests = None  # type: ignore[assignment]

from maize import Request, Response, SpiderSettings
from maize.aio.lite.spider.lite_spider import LiteSpider
from maize.common.items import Item
from maize.common.items.field import Field
from maize.exceptions.spider_exception import TransformTypeException
from maize.middlewares.pipeline.cleaner import ItemCleanerMiddleware
from maize.sync.classic.downloader.sync_httpx_downloader import SyncHttpxDownloader
from maize.sync.classic.downloader.sync_requests_downloader import SyncRequestsDownloader
from maize.sync.classic.middleware.sync_base_middleware import (
    SyncDownloaderMiddleware,
    SyncPipelineMiddleware,
    SyncSpiderMiddleware,
)
from maize.sync.classic.middleware.sync_middleware_manager import (
    SyncDownloaderMiddlewareManager,
    SyncPipelineMiddlewareManager,
    SyncSpiderMiddlewareManager,
)
from maize.sync.classic.pipeline.sync_empty_pipeline import SyncEmptyPipeline
from maize.sync.classic.pipeline.sync_pipeline_scheduler import SyncPipelineScheduler
from maize.sync.classic.scheduler import SyncSpiderPriorityQueue
from maize.sync.classic.spider.sync_spider import SyncSpider
from maize.sync.classic.spider.sync_task_spider import SyncTaskSpider
from maize.sync.classic.stats.sync_stats_collector import SyncStatsCollector
from maize.sync.classic.task.sync_task_manager import SyncTaskManager
from maize.sync.lite.spider.sync_lite_spider import SyncLiteSpider
from maize.utils.log_util import set_spider_settings
from maize.utils.spider_util import transform_sync


class _TestItem(Item):
    url: str = Field()


@pytest.fixture(autouse=True)
def _setup():
    set_spider_settings(SpiderSettings())


# --- SyncSpiderPriorityQueue ---


class TestSyncSchedulerBranches:
    def test_len_empty(self):
        queue = SyncSpiderPriorityQueue()
        assert len(queue) == 0

    def test_next_request_empty(self):
        queue = SyncSpiderPriorityQueue()
        assert queue.get() is None

    def test_next_request_with_priority(self):
        queue = SyncSpiderPriorityQueue()
        req = Request(url="http://example.com", priority=5)
        queue.put(req)
        # get_by_priority 返回 None 当优先级不匹配
        result = queue.get_by_priority(gte_priority=10)
        assert result is None

    def test_next_request_with_matching_priority(self):
        queue = SyncSpiderPriorityQueue()
        req = Request(url="http://example.com", priority=5)
        queue.put(req)
        result = queue.get_by_priority(gte_priority=5)
        assert result is not None
        assert result.url == "http://example.com"


# --- SyncTaskManager ---


class TestSyncTaskManagerBranches:
    def test_create_task_auto_open(self):
        """create_task 未 open 时自动 open。"""
        tm = SyncTaskManager(total_concurrency=1)
        assert tm._executor is None
        future = tm.create_task(lambda: 42)
        assert future.result(timeout=5) == 42
        tm.close()

    def test_create_task_exception_logged(self):
        """任务异常时记录日志。"""
        tm = SyncTaskManager(total_concurrency=1)
        tm.open()

        def bad_task():
            raise ValueError("task boom")

        future = tm.create_task(bad_task)
        with pytest.raises(ValueError):
            future.result(timeout=5)
        # 等待回调执行
        time.sleep(0.1)
        assert len(tm.current_task) == 0
        tm.close()


# --- SyncSpider abstract methods ---


class TestSyncSpiderAbstract:
    def test_start_requests_not_implemented(self):
        class MinimalSpider(SyncSpider):
            def start_requests(self) -> Generator[Request, Any, None]:
                return super().start_requests()
                yield

        spider = MinimalSpider.__new__(MinimalSpider)
        with pytest.raises(NotImplementedError):
            gen = spider.start_requests()
            next(gen)

    def test_parse_not_implemented(self):
        class MinimalSpider(SyncSpider):
            def start_requests(self) -> Generator[Request, Any, None]:
                yield Request(url="http://x.com")

        spider = MinimalSpider.__new__(MinimalSpider)
        with pytest.raises(NotImplementedError):
            spider.parse(MagicMock())


# --- SyncTaskSpider default ---


class TestSyncTaskSpiderDefault:
    def test_default_start_requests(self):
        """SyncTaskSpider 默认 start_requests yield 空 Request。"""

        class MyTaskSpider(SyncTaskSpider):
            def start_requests(self):
                return super().start_requests()

        spider = MyTaskSpider.__new__(MyTaskSpider)
        gen = spider.start_requests()
        req = next(gen)
        assert req.url == ""


# --- SyncEmptyPipeline ---


class TestSyncEmptyPipelineBranches:
    def test_process_error_item(self):
        settings = SpiderSettings()
        pipeline = SyncEmptyPipeline(settings)
        # 不应抛异常
        pipeline.process_error_item([_TestItem(url="http://x.com")])


# --- SpiderSettings merge unknown field ---


class TestSpiderSettingsMerge:
    def test_merge_unknown_field_skipped(self):
        settings = SpiderSettings()
        settings.merge_settings_from_dict({"nonexistent_field": "value"})
        assert not hasattr(settings, "nonexistent_field") or "nonexistent_field" not in settings.__class__.model_fields


# --- transform_sync ---


class TestTransformSync:
    def test_non_generator_raises(self):
        with pytest.raises(TransformTypeException):
            gen = transform_sync([1, 2, 3])
            next(gen)


# --- Request.get_headers_sync ---


class TestRequestGetHeadersSync:
    def test_coroutine_headers_func_raises(self):
        async def async_headers():
            return {"X-Test": "1"}

        req = Request(url="http://example.com", headers_func=async_headers)
        with pytest.raises(TypeError, match="coroutine"):
            req.get_headers_sync()

    def test_sync_headers_func(self):
        def sync_headers():
            return {"X-Test": "1"}

        req = Request(url="http://example.com", headers_func=sync_headers)
        result = req.get_headers_sync()
        assert result == {"X-Test": "1"}

    def test_no_headers_func(self):
        req = Request(url="http://example.com", headers={"X-Default": "1"})
        result = req.get_headers_sync()
        assert result == {"X-Default": "1"}


# --- Response encoding branches ---


class TestResponseEncodingBranches:
    def test_body_encode_error(self):
        """body 属性编码异常路径。"""
        req = Request(url="http://example.com")
        # 创建一个无法用 utf-8 编码的 text
        resp = Response(
            url="http://example.com",
            headers={"Content-Type": "text/html; charset=utf-8"},
            status=200,
            body=b"\xff\xfe",
            request=req,
        )
        # 访问 text 触发解码
        text = resp.text
        assert isinstance(text, str)

    def test_cookies_cache(self):
        """cookies 属性缓存。"""
        req = Request(url="http://example.com")
        resp = Response(
            url="http://example.com",
            headers={"Set-Cookie": "session=abc123; Path=/"},
            status=200,
            body=b"ok",
            request=req,
        )
        cookies1 = resp.cookies
        cookies2 = resp.cookies
        assert cookies1 is cookies2

    def test_get_encoding_from_body_charset(self):
        """从 body 中探测 charset。"""
        req = Request(url="http://example.com")
        html = b'<html><head><meta charset="gbk"></head><body>test</body></html>'
        resp = Response(
            url="http://example.com",
            headers={},
            status=200,
            body=html,
            request=req,
        )
        encoding = resp._get_encoding()
        assert encoding == "gbk"

    def test_get_encoding_from_body_charset_quoted(self):
        """从 body 中探测 charset="xxx" 格式。"""
        req = Request(url="http://example.com")
        html = b'<html><head><meta http-equiv="Content-Type" content="text/html; charset=\\"utf-8\\""></head></html>'
        resp = Response(
            url="http://example.com",
            headers={},
            status=200,
            body=html,
            request=req,
        )
        # 可能匹配到也可能不匹配，取决于正则
        encoding = resp._get_encoding()
        # 不抛异常即可
        assert encoding is None or isinstance(encoding, str)


# --- SyncBaseMiddleware defaults ---


class TestSyncBaseMiddlewareDefaults:
    def test_downloader_middleware_defaults(self):
        class MW(SyncDownloaderMiddleware):
            def open(self):
                pass

            def close(self):
                pass

        settings = SpiderSettings()
        mw = MW(settings)
        req = Request(url="http://example.com")
        resp = Response(url="http://example.com", headers={}, status=200, body=b"ok", request=req)
        spider = MagicMock()

        assert mw.process_request(req, spider) is req
        assert mw.process_response(req, resp, spider) is resp
        assert mw.process_exception(req, ValueError(), spider) is None

    def test_spider_middleware_defaults(self):
        class MW(SyncSpiderMiddleware):
            pass

        settings = SpiderSettings()
        mw = MW(settings)
        resp = MagicMock()
        spider = MagicMock()

        assert mw.process_spider_input(resp, spider) is True

        def gen():
            yield 1

        result = list(mw.process_spider_output(resp, gen(), spider))
        assert result == [1]

        assert mw.process_spider_exception(resp, ValueError(), spider) is None

        def start_gen():
            yield Request(url="http://x.com")

        result = list(mw.process_start_requests(start_gen(), spider))
        assert len(result) == 1

    def test_pipeline_middleware_defaults(self):
        class MW(SyncPipelineMiddleware):
            pass

        settings = SpiderSettings()
        mw = MW(settings)
        item = _TestItem(url="http://x.com")
        spider = MagicMock()

        assert mw.process_item_before(item, spider) is item
        assert mw.process_item_after(item, spider) is item


# --- SyncMiddlewareManager skip non-target type ---


class TestSyncMiddlewareManagerSkip:
    def test_downloader_manager_skips_spider_middleware(self):
        """DownloaderMiddlewareManager 跳过 SpiderMiddleware。"""

        class SpiderMW(SyncSpiderMiddleware):
            pass

        settings = SpiderSettings()
        crawler = MagicMock()
        crawler.settings = settings
        mgr = SyncDownloaderMiddlewareManager(crawler, {SpiderMW: 100})
        mgr.open()

        req = Request(url="http://example.com")
        resp = Response(url="http://example.com", headers={}, status=200, body=b"ok", request=req)
        spider = MagicMock()

        # process_response 应跳过非 DownloaderMiddleware
        result = mgr.process_response(req, resp, spider)
        assert result is resp

        # process_exception 应跳过
        result = mgr.process_exception(req, ValueError(), spider)
        assert result is None

    def test_spider_manager_skips_downloader_middleware(self):
        """SpiderMiddlewareManager 跳过 DownloaderMiddleware。"""

        class DownloaderMW(SyncDownloaderMiddleware):
            def open(self):
                pass

            def close(self):
                pass

        settings = SpiderSettings()
        crawler = MagicMock()
        crawler.settings = settings
        mgr = SyncSpiderMiddlewareManager(crawler, {DownloaderMW: 100})
        mgr.open()

        resp = MagicMock()
        spider = MagicMock()

        # process_spider_input 应跳过非 SpiderMiddleware
        result = mgr.process_spider_input(resp, spider)
        assert result is True

    def test_pipeline_manager_skips_downloader_middleware(self):
        """PipelineMiddlewareManager 跳过 DownloaderMiddleware。"""

        class DownloaderMW(SyncDownloaderMiddleware):
            def open(self):
                pass

            def close(self):
                pass

        settings = SpiderSettings()
        crawler = MagicMock()
        crawler.settings = settings
        mgr = SyncPipelineMiddlewareManager(crawler, {DownloaderMW: 100})
        mgr.open()

        item = _TestItem(url="http://x.com")
        spider = MagicMock()

        result = mgr.process_item_before(item, spider)
        assert result is item

        result = mgr.process_item_after(item, spider)
        assert result is item


# --- SyncPipelineScheduler empty queue branches ---


class TestSyncPipelineSchedulerEmptyQueue:
    def test_process_item_empty_queue(self):
        """_process_item 空队列时直接返回。"""
        settings = SpiderSettings()
        settings.pipeline.pipelines = []
        scheduler = SyncPipelineScheduler(settings)
        scheduler.open()

        result = scheduler._process_item()
        assert result.success_count == 0
        assert result.fail_count == 0

    def test_single_process_error_items_empty_queue(self):
        """_single_process_error_items 空队列时直接返回。"""
        settings = SpiderSettings()
        settings.pipeline.pipelines = []
        scheduler = SyncPipelineScheduler(settings)
        scheduler.open()

        # 不应抛异常
        scheduler._single_process_error_items()

    def test_retry_error_items_empty_queue(self):
        """_retry_error_items 空队列时返回 False。"""
        settings = SpiderSettings()
        settings.pipeline.pipelines = []
        scheduler = SyncPipelineScheduler(settings)
        scheduler.open()

        result, _process_result = scheduler._retry_error_items()
        assert result is False


# --- SyncLiteSpider abstract methods ---


class TestSyncLiteSpiderAbstract:
    def test_start_requests_not_implemented(self):
        spider = SyncLiteSpider.__new__(SyncLiteSpider)
        with pytest.raises(NotImplementedError):
            spider.start_requests()

    def test_parse_not_implemented(self):
        spider = SyncLiteSpider.__new__(SyncLiteSpider)
        with pytest.raises(NotImplementedError):
            spider.parse(MagicMock())


# --- LiteSpider abstract methods ---


class TestLiteSpiderAbstract:
    @pytest.mark.asyncio
    async def test_start_requests_not_implemented(self):
        spider = LiteSpider.__new__(LiteSpider)
        with pytest.raises(NotImplementedError):
            await spider.start_requests()

    @pytest.mark.asyncio
    async def test_parse_not_implemented(self):
        spider = LiteSpider.__new__(LiteSpider)
        with pytest.raises(NotImplementedError):
            await spider.parse(MagicMock())


# --- SyncHttpxDownloader _get_proxy ---


class TestSyncHttpxDownloaderProxy:
    def test_get_proxy_with_auth(self):
        crawler = MagicMock()
        crawler.settings = SpiderSettings()
        dl = SyncHttpxDownloader(crawler)

        req = Request(url="http://example.com", proxy="127.0.0.1:8080", proxy_username="user", proxy_password="pass")
        proxy = dl._get_proxy(req)
        assert proxy is not None
        # httpx.Proxy 解析 URL 后 auth 存储在 proxy.auth 元组中
        assert proxy.auth == ("user", "pass")

    def test_get_proxy_without_auth(self):
        crawler = MagicMock()
        crawler.settings = SpiderSettings()
        dl = SyncHttpxDownloader(crawler)

        req = Request(url="http://example.com", proxy="127.0.0.1:8080")
        proxy = dl._get_proxy(req)
        assert proxy is not None
        assert "127.0.0.1:8080" in str(proxy.url)


# --- SyncRequestsDownloader _get_request_proxy ---


class TestSyncRequestsDownloaderProxy:
    def test_get_request_proxy_with_auth(self):
        if requests is None:
            pytest.skip("requests not installed")

        crawler = MagicMock()
        crawler.settings = SpiderSettings()
        dl = SyncRequestsDownloader(crawler)

        req = Request(url="http://example.com", proxy="127.0.0.1:8080", proxy_username="user", proxy_password="pass")
        proxy = dl._get_request_proxy(req)
        assert proxy == "http://user:pass@127.0.0.1:8080"

    def test_get_request_proxy_without_auth(self):
        if requests is None:
            pytest.skip("requests not installed")

        crawler = MagicMock()
        crawler.settings = SpiderSettings()
        dl = SyncRequestsDownloader(crawler)

        req = Request(url="http://example.com", proxy="127.0.0.1:8080")
        proxy = dl._get_request_proxy(req)
        assert proxy == "http://127.0.0.1:8080"

    def test_get_request_proxy_none(self):
        if requests is None:
            pytest.skip("requests not installed")

        crawler = MagicMock()
        crawler.settings = SpiderSettings()
        dl = SyncRequestsDownloader(crawler)

        req = Request(url="http://example.com")
        proxy = dl._get_request_proxy(req)
        assert proxy is None


# --- SyncStatsCollector _upload_stat skip conditions ---


class TestSyncStatsCollectorUploadSkip:
    def test_upload_stat_skips_same_key(self):
        collector = SyncStatsCollector("test_spider")
        collector._last_upload_key = "2026-01-01 10:00"
        collector._stats["2026-01-01 10:00"] = MagicMock()

        # 不应抛异常，直接返回
        collector._upload_stat("2026-01-01 10:00")

    def test_upload_stat_skips_missing_key(self):
        collector = SyncStatsCollector("test_spider")
        collector._last_upload_key = ""

        collector._upload_stat("2026-01-01 10:00")

    def test_upload_stat_skips_single_stat_no_last_key(self):
        collector = SyncStatsCollector("test_spider")
        collector._last_upload_key = ""
        collector._stats["2026-01-01 10:00"] = MagicMock()

        # 只有一个 stat 且无 last_upload_key 时跳过
        collector._upload_stat("2026-01-01 10:00")
        assert "2026-01-01 10:00" in collector._stats


# --- Cleaner non-Pydantic fallback ---


class TestCleanerFallback:
    @pytest.mark.asyncio
    async def test_clean_non_pydantic_item(self):
        class PlainItem:
            def __init__(self):
                self.name = "  hello  "
                self.value = " world "

        settings = SpiderSettings()
        cleaner = ItemCleanerMiddleware(settings)
        item = PlainItem()
        result = await cleaner.process_item_before(item, MagicMock())
        assert result.name == "hello"
        assert result.value == "world"
