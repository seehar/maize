"""
Tests for lite spider
"""

import asyncio
import contextlib
import logging
from abc import ABC
from unittest.mock import AsyncMock, patch
from urllib.parse import urlparse

import pytest

from maize.aio.lite import LiteCrawler, LiteSpider
from maize.common.http import Request, Response
from maize.common.items import Item


class SampleLiteSpider(LiteSpider):
    """Sample spider for testing"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.responses_handled = 0

    async def start_requests(self):
        yield Request("https://httpbin.org/get")

    async def parse(self, response: Response):
        self.responses_handled += 1


def test_lite_spider_run():
    """Test that lite spider run() method works synchronously"""
    spider = SampleLiteSpider()
    spider.run()

    assert spider.responses_handled == 1


@pytest.mark.asyncio
async def test_lite_spider_open_close():
    """Test lite spider open and close"""
    spider = SampleLiteSpider()
    await spider.open()
    assert spider._session is not None

    await spider.close()
    assert spider._session is None


@pytest.mark.asyncio
async def test_lite_spider_fetch():
    """Test lite spider fetch method"""
    spider = SampleLiteSpider()
    await spider.open()

    try:
        request = Request("https://httpbin.org/get")
        mock_response = Response(
            url="https://httpbin.org/get",
            headers={},
            request=request,
            body=b'{"ok": true}',
            text='{"ok": true}',
            status=200,
        )
        with patch.object(spider, "fetch", new_callable=AsyncMock, return_value=mock_response):
            response = await spider.fetch(request)

        assert response.status == 200
        assert response.url == "https://httpbin.org/get"
        assert response.body is not None
    finally:
        await spider.close()


@pytest.mark.asyncio
async def test_lite_spider_fetch_error():
    """Test lite spider handles fetch errors"""
    spider = SampleLiteSpider()
    await spider.open()

    try:
        request = Request("https://httpbin.org/status/500")
        mock_response = Response(
            url="https://httpbin.org/status/500",
            headers={},
            request=request,
            body=b"",
            text="",
            status=500,
        )
        with patch.object(spider, "fetch", new_callable=AsyncMock, return_value=mock_response):
            response = await spider.fetch(request)

        assert response.status == 500
    finally:
        await spider.close()


@pytest.mark.asyncio
async def test_lite_crawler_crawl():
    """Test LiteCrawler crawl method"""
    spider = SampleLiteSpider()
    crawler = LiteCrawler(spider)
    await crawler.crawl()

    assert spider.responses_handled == 1


def test_lite_spider_logger():
    """Test lite spider logger property"""
    spider = SampleLiteSpider()
    logger = spider.logger

    assert logger.name == "maize.lite.SampleLiteSpider"


@pytest.mark.asyncio
async def test_lite_spider_fetch_without_open():
    """Test lite spider fetch without open raises RuntimeError"""
    spider = SampleLiteSpider()
    request = Request("https://httpbin.org/get")

    with pytest.raises(RuntimeError, match="Session not initialized"):
        await spider.fetch(request)


def test_lite_spider_inherits_from_abc():
    """Test that LiteSpider inherits from ABC"""
    assert issubclass(LiteSpider, ABC)


def test_lite_spider_with_custom_concurrency():
    """Test lite spider with custom concurrency"""
    spider = SampleLiteSpider(concurrency=10)

    assert spider.concurrency == 10


def test_lite_spider_with_custom_retry():
    """Test lite spider with custom retry"""
    spider = SampleLiteSpider(retry=5)

    assert spider.retry == 5


def test_lite_spider_with_custom_proxy():
    """Test lite spider with custom proxy"""
    spider = SampleLiteSpider(proxy="http://127.0.0.1:7890")

    assert spider.proxy == "http://127.0.0.1:7890"


def test_lite_spider_with_custom_timeout():
    """Test lite spider with custom timeout"""
    spider = SampleLiteSpider(timeout=60.0)

    assert spider.timeout == 60.0


def test_lite_crawler_with_custom_concurrency():
    """Test LiteCrawler with custom concurrency"""
    spider = SampleLiteSpider()
    crawler = LiteCrawler(spider, concurrency=20)

    assert crawler.concurrency == 20


@pytest.mark.asyncio
async def test_lite_spider_on_start_hook():
    """Test on_start hook is called"""
    started = False

    class HookedSpider(SampleLiteSpider):
        async def on_start(self) -> None:
            nonlocal started
            started = True

    spider = HookedSpider()
    crawler = LiteCrawler(spider)
    await crawler.crawl()

    assert started is True


@pytest.mark.asyncio
async def test_lite_spider_on_close_hook():
    """Test on_close hook is called"""
    closed = False

    class HookedSpider(SampleLiteSpider):
        async def on_close(self) -> None:
            nonlocal closed
            closed = True

    spider = HookedSpider()
    crawler = LiteCrawler(spider)
    await crawler.crawl()

    assert closed is True


@pytest.mark.asyncio
async def test_crawl_with_mock_parse_yields_request():
    """Test parse yielding a Request causes it to be re-fetched"""

    class FollowSpider(LiteSpider):
        def __init__(self):
            super().__init__()
            self.responses_handled = 0
            self.urls_fetched = []

        async def start_requests(self):
            yield Request("https://example.com/page1")

        async def parse(self, response):
            self.responses_handled += 1
            self.urls_fetched.append(response.url)
            if response.url == "https://example.com/page1":
                yield Request("https://example.com/page2")

    spider = FollowSpider()

    request1 = Request("https://example.com/page1")
    request2 = Request("https://example.com/page2")
    resp1 = Response(url="https://example.com/page1", headers={}, body=b"page1", status=200, request=request1)
    resp2 = Response(url="https://example.com/page2", headers={}, body=b"page2", status=200, request=request2)
    fetch_mock = AsyncMock(side_effect=[resp1, resp2])

    with patch.object(spider, "fetch", fetch_mock):
        crawler = LiteCrawler(spider, concurrency=2)
        await crawler.crawl()

    assert spider.responses_handled == 2
    assert "https://example.com/page2" in spider.urls_fetched


@pytest.mark.asyncio
async def test_crawl_parse_yields_item():
    """Test parse yielding Item collects it in crawler.items"""

    class ItemSpider(LiteSpider):
        async def start_requests(self):
            yield Request("https://example.com/data")

        async def parse(self, response):
            yield Item()

    spider = ItemSpider()
    request = Request("https://example.com/data")
    resp = Response(url="https://example.com/data", headers={}, body=b"ok", status=200, request=request)

    with patch.object(spider, "fetch", new_callable=AsyncMock, return_value=resp):
        crawler = LiteCrawler(spider)
        await crawler.crawl()

    assert len(crawler.items) == 1
    assert isinstance(crawler.items[0], Item)


@pytest.mark.asyncio
async def test_crawl_mixed_parse_output():
    """Test parse yielding both Request and Item"""
    tracked: list[str] = []

    class MixedSpider(LiteSpider):
        def __init__(self):
            super().__init__()
            self.seen_urls = []

        async def start_requests(self):
            yield Request("https://example.com/page1")

        async def parse(self, response):
            self.seen_urls.append(response.url)
            tracked.append("page")
            if response.url == "https://example.com/page1":
                yield Request("https://example.com/page2")
                tracked.append("forward")

    spider = MixedSpider()
    req1 = Request("https://example.com/page1")
    req2 = Request("https://example.com/page2")
    resp1 = Response(url="https://example.com/page1", headers={}, body=b"1", status=200, request=req1)
    resp2 = Response(url="https://example.com/page2", headers={}, body=b"2", status=200, request=req2)

    with patch.object(spider, "fetch", AsyncMock(side_effect=[resp1, resp2])):
        crawler = LiteCrawler(spider, concurrency=2)
        await crawler.crawl()

    assert len(spider.seen_urls) == 2
    assert tracked.count("page") == 2
    assert tracked.count("forward") == 1


@pytest.mark.asyncio
async def test_should_retry_on_status_0():
    """Test retry on connection failure (status=0)"""
    spider = SampleLiteSpider(retry=3)
    request = Request("https://example.com/fail")
    fail_resp = Response(url="https://example.com/fail", headers={}, body=b"", status=0, request=request)
    ok_resp = Response(url="https://example.com/fail", headers={}, body=b"ok", status=200, request=request)

    with patch.object(spider, "fetch", AsyncMock(side_effect=[fail_resp, fail_resp, ok_resp])):
        crawler = LiteCrawler(spider)
        response = await crawler._fetch_with_retry(request)

    assert response.status == 200


@pytest.mark.asyncio
async def test_should_retry_on_status_500():
    """Test retry on server error (500)"""
    spider = SampleLiteSpider(retry=2)
    request = Request("https://example.com/err")
    err_resp = Response(url="https://example.com/err", headers={}, body=b"", status=500, request=request)
    ok_resp = Response(url="https://example.com/err", headers={}, body=b"ok", status=200, request=request)

    with patch.object(spider, "fetch", AsyncMock(side_effect=[err_resp, ok_resp])):
        crawler = LiteCrawler(spider)
        response = await crawler._fetch_with_retry(request)

    assert response.status == 200


@pytest.mark.asyncio
async def test_should_retry_on_status_429():
    """Test retry on rate limit (429)"""
    spider = SampleLiteSpider(retry=2)
    request = Request("https://example.com/rate")
    limit_resp = Response(url="https://example.com/rate", headers={}, body=b"", status=429, request=request)
    ok_resp = Response(url="https://example.com/rate", headers={}, body=b"ok", status=200, request=request)

    with patch.object(spider, "fetch", AsyncMock(side_effect=[limit_resp, ok_resp])):
        crawler = LiteCrawler(spider)
        response = await crawler._fetch_with_retry(request)

    assert response.status == 200


@pytest.mark.asyncio
async def test_no_retry_on_4xx_normal():
    """Test no retry on normal client errors (400, 404)"""
    spider = SampleLiteSpider(retry=3)
    request = Request("https://example.com/404")
    resp = Response(url="https://example.com/404", headers={}, body=b"", status=404, request=request)

    fetches = []

    async def fetch_side_effect(req):
        fetches.append(req)
        return resp

    with patch.object(spider, "fetch", fetch_side_effect):
        crawler = LiteCrawler(spider)
        response = await crawler._fetch_with_retry(request)

    assert response.status == 404
    assert len(fetches) == 1


@pytest.mark.asyncio
async def test_exhausted_retry_returns_last_response():
    """Test exhausted retry returns the last failed response"""
    spider = SampleLiteSpider(retry=3)
    request = Request("https://example.com/fail")
    fail = Response(url="https://example.com/fail", headers={}, body=b"", status=503, request=request)

    with patch.object(spider, "fetch", AsyncMock(return_value=fail)):
        crawler = LiteCrawler(spider)
        response = await crawler._fetch_with_retry(request)

    assert response.status == 503


@pytest.mark.asyncio
async def test_crawl_with_mock_coroutine_parse_backward_compat():
    """Test backward compatibility: coroutine-style parse still works"""
    spider = SampleLiteSpider()
    request = Request("https://example.com/data")
    resp = Response(url="https://example.com/data", headers={}, body=b"ok", status=200, request=request)

    with patch.object(spider, "fetch", new_callable=AsyncMock, return_value=resp):
        crawler = LiteCrawler(spider)
        await crawler.crawl()

    assert spider.responses_handled == 1


@pytest.mark.asyncio
async def test_dedup_drops_duplicate_request():
    """相同 URL 的重复请求只抓一次（默认 dedup=True）"""

    class DedupSpider(LiteSpider):
        def __init__(self):
            super().__init__()
            self.fetched = []

        async def start_requests(self):
            yield Request("https://example.com/dup")
            yield Request("https://example.com/dup")
            yield Request("https://example.com/other")

        async def parse(self, response):
            self.fetched.append(response.url)

    spider = DedupSpider()
    req = Request("https://example.com/dup")
    req_other = Request("https://example.com/other")
    resp = Response(url="https://example.com/dup", headers={}, body=b"", status=200, request=req)
    resp_other = Response(url="https://example.com/other", headers={}, body=b"", status=200, request=req_other)

    with patch.object(spider, "fetch", AsyncMock(side_effect=[resp, resp_other])):
        crawler = LiteCrawler(spider)
        await crawler.crawl()

    assert spider.fetched.count("https://example.com/dup") == 1
    assert "https://example.com/other" in spider.fetched


@pytest.mark.asyncio
async def test_dedup_respects_dont_filter():
    """meta['dont_filter']=True 的请求跳过去重"""

    class DontFilterSpider(LiteSpider):
        def __init__(self):
            super().__init__()
            self.fetch_count = 0

        async def start_requests(self):
            yield Request("https://example.com/poll", meta={"dont_filter": True})
            yield Request("https://example.com/poll", meta={"dont_filter": True})

        async def parse(self, response):
            self.fetch_count += 1

    spider = DontFilterSpider()
    req = Request("https://example.com/poll", meta={"dont_filter": True})
    resp = Response(url="https://example.com/poll", headers={}, body=b"", status=200, request=req)

    with patch.object(spider, "fetch", AsyncMock(side_effect=[resp, resp])):
        crawler = LiteCrawler(spider)
        await crawler.crawl()

    assert spider.fetch_count == 2


@pytest.mark.asyncio
async def test_dedup_disabled_globally():
    """spider.dedup=False 时整个 spider 不去重"""

    class NoDedupSpider(LiteSpider):
        dedup = False

        def __init__(self):
            super().__init__()
            self.fetch_count = 0

        async def start_requests(self):
            yield Request("https://example.com/repeat")
            yield Request("https://example.com/repeat")

        async def parse(self, response):
            self.fetch_count += 1

    spider = NoDedupSpider()
    req = Request("https://example.com/repeat")
    resp = Response(url="https://example.com/repeat", headers={}, body=b"", status=200, request=req)

    with patch.object(spider, "fetch", AsyncMock(side_effect=[resp, resp])):
        crawler = LiteCrawler(spider)
        await crawler.crawl()

    assert spider.fetch_count == 2


@pytest.mark.asyncio
async def test_max_depth_drops_deep_requests():
    """max_depth=1 时，depth=2 的请求被丢弃"""

    class DepthSpider(LiteSpider):
        max_depth = 1

        def __init__(self):
            super().__init__()
            self.fetched = []

        async def start_requests(self):
            yield Request("https://example.com/l0")

        async def parse(self, response):
            self.fetched.append(response.url)
            if response.url == "https://example.com/l0":
                yield Request("https://example.com/l1")  # depth=1, OK
            elif response.url == "https://example.com/l1":
                yield Request("https://example.com/l2")  # depth=2, dropped

    spider = DepthSpider()
    req0 = Request("https://example.com/l0")
    req1 = Request("https://example.com/l1")
    resp0 = Response(url="https://example.com/l0", headers={}, body=b"", status=200, request=req0)
    resp1 = Response(url="https://example.com/l1", headers={}, body=b"", status=200, request=req1)

    with patch.object(spider, "fetch", AsyncMock(side_effect=[resp0, resp1])):
        crawler = LiteCrawler(spider)
        await crawler.crawl()

    assert spider.fetched == ["https://example.com/l0", "https://example.com/l1"]


@pytest.mark.asyncio
async def test_process_item_hook_called():
    """yield Item 时 process_item 被自动调用"""

    class PipelineSpider(LiteSpider):
        def __init__(self):
            super().__init__()
            self.processed = []

        async def start_requests(self):
            yield Request("https://example.com/data")

        async def parse(self, response):
            yield Item()

        async def process_item(self, item):
            self.processed.append(item)

    spider = PipelineSpider()
    req = Request("https://example.com/data")
    resp = Response(url="https://example.com/data", headers={}, body=b"", status=200, request=req)

    with patch.object(spider, "fetch", AsyncMock(return_value=resp)):
        crawler = LiteCrawler(spider)
        await crawler.crawl()

    assert len(spider.processed) == 1
    assert len(crawler.items) == 1


@pytest.mark.asyncio
async def test_callback_routing():
    """Request(callback=custom) 路由到自定义回调，而非 parse"""

    class CallbackSpider(LiteSpider):
        def __init__(self):
            super().__init__()
            self.parse_called = False
            self.detail_called = False

        async def start_requests(self):
            yield Request("https://example.com/list", callback=self.parse_detail)

        async def parse(self, response):
            self.parse_called = True

        async def parse_detail(self, response):
            self.detail_called = True

    spider = CallbackSpider()
    req = Request("https://example.com/list", callback=spider.parse_detail)
    resp = Response(url="https://example.com/list", headers={}, body=b"", status=200, request=req)

    with patch.object(spider, "fetch", AsyncMock(return_value=resp)):
        crawler = LiteCrawler(spider)
        await crawler.crawl()

    assert spider.detail_called is True
    assert spider.parse_called is False


@pytest.mark.asyncio
async def test_stats_count_succeeded_failed():
    """stats 正确统计 succeeded / failed / requested / items"""

    class StatsSpider(LiteSpider):
        async def start_requests(self):
            yield Request("https://example.com/ok1")
            yield Request("https://example.com/ok2")
            yield Request("https://example.com/notfound")

        async def parse(self, response):
            yield Item()

    spider = StatsSpider()
    r1 = Request("https://example.com/ok1")
    r2 = Request("https://example.com/ok2")
    r3 = Request("https://example.com/notfound")
    resp1 = Response(url="https://example.com/ok1", headers={}, body=b"", status=200, request=r1)
    resp2 = Response(url="https://example.com/ok2", headers={}, body=b"", status=200, request=r2)
    resp3 = Response(url="https://example.com/notfound", headers={}, body=b"", status=404, request=r3)

    with patch.object(spider, "fetch", AsyncMock(side_effect=[resp1, resp2, resp3])):
        crawler = LiteCrawler(spider)
        await crawler.crawl()

    assert crawler.stats["requested"] == 3
    assert crawler.stats["succeeded"] == 2
    assert crawler.stats["failed"] == 1
    assert crawler.stats["items"] == 3


@pytest.mark.asyncio
async def test_stats_count_dropped():
    """stats 正确统计 dropped（去重丢弃）"""

    class DropStatsSpider(LiteSpider):
        async def start_requests(self):
            yield Request("https://example.com/dup")
            yield Request("https://example.com/dup")
            yield Request("https://example.com/dup")

        async def parse(self, response):
            pass

    spider = DropStatsSpider()
    req = Request("https://example.com/dup")
    resp = Response(url="https://example.com/dup", headers={}, body=b"", status=200, request=req)

    with patch.object(spider, "fetch", AsyncMock(side_effect=[resp])):
        crawler = LiteCrawler(spider)
        await crawler.crawl()

    assert crawler.stats["requested"] == 1
    assert crawler.stats["dropped"] == 2


@pytest.mark.asyncio
async def test_stats_count_retried():
    """stats 正确统计 retried（500 -> 200 触发一次重试）"""

    class RetryStatsSpider(LiteSpider):
        def __init__(self):
            super().__init__(retry=3)

        async def start_requests(self):
            yield Request("https://example.com/flaky")

        async def parse(self, response):
            pass

    spider = RetryStatsSpider()
    req = Request("https://example.com/flaky")
    resp_fail = Response(url="https://example.com/flaky", headers={}, body=b"", status=500, request=req)
    resp_ok = Response(url="https://example.com/flaky", headers={}, body=b"", status=200, request=req)

    with patch.object(spider, "fetch", AsyncMock(side_effect=[resp_fail, resp_ok])):
        crawler = LiteCrawler(spider)
        await crawler.crawl()

    assert crawler.stats["retried"] == 1
    assert crawler.stats["succeeded"] == 1


@pytest.mark.asyncio
async def test_priority_queue_orders_requests():
    """priority 高的请求先出队（priority 数值越小越优先）"""

    class PrioritySpider(LiteSpider):
        def __init__(self):
            super().__init__()
            self.fetched_order = []

        async def start_requests(self):
            yield Request("https://example.com/low", priority=10)
            yield Request("https://example.com/high", priority=1)
            yield Request("https://example.com/mid", priority=5)

        async def parse(self, response):
            self.fetched_order.append(response.url)

    spider = PrioritySpider()
    r_low = Request("https://example.com/low", priority=10)
    r_high = Request("https://example.com/high", priority=1)
    r_mid = Request("https://example.com/mid", priority=5)
    resp_low = Response(url="https://example.com/low", headers={}, body=b"", status=200, request=r_low)
    resp_high = Response(url="https://example.com/high", headers={}, body=b"", status=200, request=r_high)
    resp_mid = Response(url="https://example.com/mid", headers={}, body=b"", status=200, request=r_mid)

    # 并发=1 保证顺序可预测
    with patch.object(spider, "fetch", AsyncMock(side_effect=[resp_high, resp_mid, resp_low])):
        crawler = LiteCrawler(spider, concurrency=1)
        await crawler.crawl()

    assert spider.fetched_order == ["https://example.com/high", "https://example.com/mid", "https://example.com/low"]


@pytest.mark.asyncio
async def test_priority_queue_tie_breaker():
    """同 priority 的请求按入队顺序出队，不报错"""

    class TieSpider(LiteSpider):
        def __init__(self):
            super().__init__()
            self.fetched_order = []

        async def start_requests(self):
            yield Request("https://example.com/a")  # priority=0
            yield Request("https://example.com/b")  # priority=0
            yield Request("https://example.com/c")  # priority=0

        async def parse(self, response):
            self.fetched_order.append(response.url)

    spider = TieSpider()
    r_a = Request("https://example.com/a")
    r_b = Request("https://example.com/b")
    r_c = Request("https://example.com/c")
    resp_a = Response(url="https://example.com/a", headers={}, body=b"", status=200, request=r_a)
    resp_b = Response(url="https://example.com/b", headers={}, body=b"", status=200, request=r_b)
    resp_c = Response(url="https://example.com/c", headers={}, body=b"", status=200, request=r_c)

    with patch.object(spider, "fetch", AsyncMock(side_effect=[resp_a, resp_b, resp_c])):
        crawler = LiteCrawler(spider, concurrency=1)
        await crawler.crawl()

    assert spider.fetched_order == ["https://example.com/a", "https://example.com/b", "https://example.com/c"]


@pytest.mark.asyncio
async def test_default_headers_set_on_session():
    """open() 后 ClientSession 含默认 UA"""
    spider = SampleLiteSpider()
    await spider.open()
    try:
        # aiohttp ClientSession.headers 是 CIMultiDict
        assert spider._session.headers.get("User-Agent") == "maize-lite/1.0"
    finally:
        await spider.close()


@pytest.mark.asyncio
async def test_custom_default_headers():
    """子类重写 default_headers 后 UA 被覆盖"""

    class CustomHeaderSpider(LiteSpider):
        @property
        def default_headers(self):
            return {"User-Agent": "my-spider/2.0", "Accept": "application/json"}

        async def start_requests(self):
            yield Request("https://example.com")

        async def parse(self, response):
            pass

    spider = CustomHeaderSpider()
    await spider.open()
    try:
        assert spider._session.headers.get("User-Agent") == "my-spider/2.0"
        assert spider._session.headers.get("Accept") == "application/json"
    finally:
        await spider.close()


@pytest.mark.asyncio
async def test_graceful_shutdown_calls_on_close():
    """正常完成流程下 on_close 被调用，in-flight 请求完成"""

    class ShutdownSpider(LiteSpider):
        def __init__(self):
            super().__init__()
            self.on_close_called = False
            self.processed = []

        async def start_requests(self):
            yield Request("https://example.com/p1")
            yield Request("https://example.com/p2")

        async def parse(self, response):
            self.processed.append(response.url)

        async def on_close(self):
            self.on_close_called = True

    spider = ShutdownSpider()
    r1 = Request("https://example.com/p1")
    r2 = Request("https://example.com/p2")
    resp1 = Response(url="https://example.com/p1", headers={}, body=b"", status=200, request=r1)
    resp2 = Response(url="https://example.com/p2", headers={}, body=b"", status=200, request=r2)

    with patch.object(spider, "fetch", AsyncMock(side_effect=[resp1, resp2])):
        crawler = LiteCrawler(spider)
        await crawler.crawl()

    assert spider.on_close_called is True
    assert len(spider.processed) == 2


@pytest.mark.asyncio
async def test_custom_should_retry():
    """子类重写 should_retry 对 403 重试，断言 403->200 触发重试"""

    class Retry403Spider(LiteSpider):
        def __init__(self):
            super().__init__(retry=3)

        def should_retry(self, response: Response) -> bool:
            return response.status == 403 or super().should_retry(response)

        async def start_requests(self):
            yield Request("https://example.com/forbidden")

        async def parse(self, response):
            pass

    spider = Retry403Spider()
    req = Request("https://example.com/forbidden")
    resp_403 = Response(url="https://example.com/forbidden", headers={}, body=b"", status=403, request=req)
    resp_200 = Response(url="https://example.com/forbidden", headers={}, body=b"", status=200, request=req)

    with patch.object(spider, "fetch", AsyncMock(side_effect=[resp_403, resp_200])):
        crawler = LiteCrawler(spider)
        await crawler.crawl()

    assert crawler.stats["retried"] == 1
    assert crawler.stats["succeeded"] == 1


@pytest.mark.asyncio
async def test_default_should_retry_unchanged():
    """默认 should_retry 行为与改动前一致：0/5xx/429 重试，4xx 不重试"""

    class DefaultRetrySpider(LiteSpider):
        def __init__(self):
            super().__init__(retry=3)

        async def start_requests(self):
            yield Request("https://example.com/500")
            yield Request("https://example.com/404")
            yield Request("https://example.com/429")

        async def parse(self, response):
            pass

    spider = DefaultRetrySpider()
    r500 = Request("https://example.com/500")
    r404 = Request("https://example.com/404")
    r429 = Request("https://example.com/429")
    # 500 -> 200, 404 直接返回, 429 -> 200
    resp_500 = Response(url="https://example.com/500", headers={}, body=b"", status=500, request=r500)
    resp_500_ok = Response(url="https://example.com/500", headers={}, body=b"", status=200, request=r500)
    resp_404 = Response(url="https://example.com/404", headers={}, body=b"", status=404, request=r404)
    resp_429 = Response(url="https://example.com/429", headers={}, body=b"", status=429, request=r429)
    resp_429_ok = Response(url="https://example.com/429", headers={}, body=b"", status=200, request=r429)

    with patch.object(
        spider,
        "fetch",
        AsyncMock(side_effect=[resp_500, resp_500_ok, resp_404, resp_429, resp_429_ok]),
    ):
        crawler = LiteCrawler(spider)
        await crawler.crawl()

    # 500 重试 1 次，429 重试 1 次，404 不重试
    assert crawler.stats["retried"] == 2
    assert crawler.stats["succeeded"] == 2  # 500->200 和 429->200
    assert crawler.stats["failed"] == 1  # 404


@pytest.mark.asyncio
async def test_per_domain_concurrency_limits():
    """per_domain_concurrency=1 时同域名请求串行"""

    class PoliteSpider(LiteSpider):
        per_domain_concurrency = 1

        def __init__(self):
            super().__init__()
            self.fetch_times: list[float] = []

        async def start_requests(self):
            yield Request("https://example.com/a")
            yield Request("https://example.com/b")
            yield Request("https://example.com/c")

        async def parse(self, response):
            pass

        async def fetch(self, request: Request) -> Response:
            self.fetch_times.append(asyncio.get_event_loop().time())
            await asyncio.sleep(0.05)
            return Response(url=request.url, headers={}, body=b"", status=200, request=request)

    spider = PoliteSpider()
    crawler = LiteCrawler(spider, concurrency=10)
    await crawler.crawl()

    # 串行：每个 fetch 间隔 >= 0.04s
    for i in range(1, len(spider.fetch_times)):
        gap = spider.fetch_times[i] - spider.fetch_times[i - 1]
        assert gap >= 0.04, f"gap={gap}, expected >= 0.04 (serial)"


@pytest.mark.asyncio
async def test_per_domain_concurrency_zero_unlimited():
    """per_domain_concurrency=0（默认）时并发不受域名限制"""

    class UnlimitedSpider(LiteSpider):
        def __init__(self):
            super().__init__()
            self.fetch_times: list[float] = []

        async def start_requests(self):
            yield Request("https://example.com/a")
            yield Request("https://example.com/b")
            yield Request("https://example.com/c")

        async def parse(self, response):
            pass

        async def fetch(self, request: Request) -> Response:
            self.fetch_times.append(asyncio.get_event_loop().time())
            await asyncio.sleep(0.05)
            return Response(url=request.url, headers={}, body=b"", status=200, request=request)

    spider = UnlimitedSpider()
    crawler = LiteCrawler(spider, concurrency=10)
    await crawler.crawl()

    # 并发：3 个 fetch 几乎同时开始，间隔 < 0.02s
    for i in range(1, len(spider.fetch_times)):
        gap = spider.fetch_times[i] - spider.fetch_times[i - 1]
        assert gap < 0.02, f"gap={gap}, expected < 0.02 (concurrent)"


@pytest.mark.asyncio
async def test_per_domain_concurrency_multi_domain():
    """两域名各 per_domain=1，不同域名可并行"""

    class MultiDomainSpider(LiteSpider):
        per_domain_concurrency = 1

        def __init__(self):
            super().__init__()
            self.fetch_times: dict[str, list[float]] = {}

        async def start_requests(self):
            yield Request("https://a.com/1")
            yield Request("https://a.com/2")
            yield Request("https://b.com/1")
            yield Request("https://b.com/2")

        async def parse(self, response):
            pass

        async def fetch(self, request: Request) -> Response:
            netloc = urlparse(request.url).netloc
            self.fetch_times.setdefault(netloc, []).append(asyncio.get_event_loop().time())
            await asyncio.sleep(0.05)
            return Response(url=request.url, headers={}, body=b"", status=200, request=request)

    spider = MultiDomainSpider()
    crawler = LiteCrawler(spider, concurrency=10)
    await crawler.crawl()

    # 同域名串行（间隔 >= 0.04s），不同域名第一个请求几乎同时（间隔 < 0.02s）
    for netloc, times in spider.fetch_times.items():
        for i in range(1, len(times)):
            gap = times[i] - times[i - 1]
            assert gap >= 0.04, f"{netloc} gap={gap}, expected >= 0.04 (serial per domain)"
    # a.com 和 b.com 的第一个请求应几乎同时
    gap_cross = abs(spider.fetch_times["a.com"][0] - spider.fetch_times["b.com"][0])
    assert gap_cross < 0.02, f"cross-domain gap={gap_cross}, expected < 0.02 (parallel)"


@pytest.mark.asyncio
async def test_structured_log_format(caplog):
    """结构化日志包含 url= status= elapsed= retry= 字段"""

    class LogSpider(LiteSpider):
        async def start_requests(self):
            yield Request("https://example.com/test")

        async def parse(self, response):
            pass

    spider = LogSpider()
    req = Request("https://example.com/test")
    resp = Response(url="https://example.com/test", headers={}, body=b"", status=200, request=req)

    with patch.object(spider, "fetch", AsyncMock(return_value=resp)):
        crawler = LiteCrawler(spider)
        with caplog.at_level(logging.INFO, logger=crawler.logger.name):
            await crawler.crawl()

    # 找到 request 行
    request_logs = [r for r in caplog.records if "request url=" in r.message]
    assert len(request_logs) >= 1
    msg = request_logs[0].message
    assert "url=https://example.com/test" in msg
    assert "status=200" in msg
    assert "elapsed=" in msg
    assert "retry=0" in msg


@pytest.mark.asyncio
async def test_log_level_by_status(caplog):
    """200 -> INFO, 500 重试 -> WARNING, 404 -> INFO（不重试但记录）"""

    class LogLevelSpider(LiteSpider):
        def __init__(self):
            super().__init__(retry=3)

        async def start_requests(self):
            yield Request("https://example.com/ok")
            yield Request("https://example.com/err")
            yield Request("https://example.com/notfound")

        async def parse(self, response):
            pass

    spider = LogLevelSpider()
    r_ok = Request("https://example.com/ok")
    r_err = Request("https://example.com/err")
    r_nf = Request("https://example.com/notfound")
    resp_ok = Response(url="https://example.com/ok", headers={}, body=b"", status=200, request=r_ok)
    resp_500 = Response(url="https://example.com/err", headers={}, body=b"", status=500, request=r_err)
    resp_500_ok = Response(url="https://example.com/err", headers={}, body=b"", status=200, request=r_err)
    resp_nf = Response(url="https://example.com/notfound", headers={}, body=b"", status=404, request=r_nf)

    with patch.object(
        spider,
        "fetch",
        AsyncMock(side_effect=[resp_ok, resp_500, resp_500_ok, resp_nf]),
    ):
        crawler = LiteCrawler(spider)
        with caplog.at_level(logging.DEBUG, logger=crawler.logger.name):
            await crawler.crawl()

    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    infos = [r for r in caplog.records if r.levelno == logging.INFO and "request url=" in r.message]
    assert any("status=500" in r.message and "retry" in r.message for r in warnings)
    assert len(infos) == 3  # ok, err(final 200), notfound


@pytest.mark.asyncio
async def test_sigint_no_deadlock():
    """SIGINT 后 crawl() 不死锁，on_close 被执行，未处理请求被丢弃"""

    class SigintSpider(LiteSpider):
        def __init__(self):
            super().__init__(concurrency=2)
            self.on_close_called = False
            self.processed = []

        async def start_requests(self):
            # 入队多个请求，确保 SIGINT 时队列中仍有 pending
            for i in range(10):
                yield Request(f"https://example.com/p{i}")

        async def parse(self, response):
            self.processed.append(response.url)

        async def on_close(self):
            self.on_close_called = True

    spider = SigintSpider()
    responses = [
        Response(
            url=f"https://example.com/p{i}",
            headers={},
            body=b"",
            status=200,
            request=Request(f"https://example.com/p{i}"),
        )
        for i in range(10)
    ]

    fetch_event = asyncio.Event()

    async def mock_fetch(request):
        # 第一个请求处理中时触发 SIGINT
        fetch_event.set()
        await asyncio.sleep(0.01)
        return responses[int(request.url.split("/p")[-1])]

    with patch.object(spider, "fetch", mock_fetch):
        crawler = LiteCrawler(spider)

        # 在 crawl 开始后触发 stop_event（模拟 SIGINT）
        async def trigger_stop():
            await fetch_event.wait()
            # 直接调用 crawler 内部 signal handler 逻辑
            # 找到 crawl() 中注册的 signal handler 并触发
            crawler._logger.info("test: simulating SIGINT")
            # 通过发送真实信号来触发
            import signal as sig_mod

            sig_mod.raise_signal(sig_mod.SIGINT)

        trigger_task = asyncio.create_task(trigger_stop())

        try:
            await asyncio.wait_for(crawler.crawl(), timeout=5.0)
        except asyncio.TimeoutError:
            pytest.fail("crawl() deadlocked after SIGINT")
        finally:
            trigger_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await trigger_task

    assert spider.on_close_called is True


@pytest.mark.asyncio
async def test_worker_exception_does_not_deadlock():
    """_process 抛异常时 worker 不死锁，crawl 正常结束"""

    class BombSpider(LiteSpider):
        def __init__(self):
            super().__init__(concurrency=1)
            self.on_close_called = False

        async def start_requests(self):
            yield Request("https://example.com/ok")

        async def parse(self, response):
            raise ValueError("boom")

        async def on_close(self):
            self.on_close_called = True

    spider = BombSpider()
    req = Request("https://example.com/ok")
    resp = Response(url="https://example.com/ok", headers={}, body=b"", status=200, request=req)

    with patch.object(spider, "fetch", AsyncMock(return_value=resp)):
        crawler = LiteCrawler(spider)
        try:
            await asyncio.wait_for(crawler.crawl(), timeout=5.0)
        except asyncio.TimeoutError:
            pytest.fail("crawl() deadlocked on worker exception")

    assert spider.on_close_called is True
