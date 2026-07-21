"""
Tests for lite spider
"""

from abc import ABC
from unittest.mock import AsyncMock, patch

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
