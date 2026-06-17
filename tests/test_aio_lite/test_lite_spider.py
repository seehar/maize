"""
Tests for lite spider
"""

import pytest

from maize.aio.lite import LiteCrawler, LiteSpider
from maize.common.http import Request, Response


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
    from abc import ABC

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
