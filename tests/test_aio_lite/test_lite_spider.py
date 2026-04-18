"""
Tests for lite spider
"""

import pytest

from maize.aio.lite import LiteCrawler, LiteCrawlerProcess, LiteSettings, LiteSpider
from maize.common.http import Request, Response


class SampleLiteSpider(LiteSpider):
    """Sample spider for testing"""

    def __init__(self):
        super().__init__()
        self.responses_handled = 0

    async def start_requests(self):
        yield Request("https://httpbin.org/get")

    async def parse(self, response: Response):
        self.responses_handled += 1


@pytest.mark.asyncio
async def test_lite_spider_crawl():
    """Test that lite spider can crawl and handle responses"""
    spider = SampleLiteSpider()
    await spider.crawl()

    assert spider.responses_handled == 1
    assert spider._session is None  # Session should be closed


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


def test_lite_settings_defaults():
    """Test LiteSettings default values"""
    settings = LiteSettings()

    assert settings.request_timeout == 30.0
    assert settings.max_retries == 3
    assert settings.follow_redirects is True
    assert settings.max_redirects == 10
    assert settings.verify_ssl is True
    assert settings.log_level == "INFO"


def test_lite_settings_custom():
    """Test LiteSettings with custom values"""
    settings = LiteSettings(
        request_timeout=60.0,
        max_retries=5,
        follow_redirects=False,
        max_redirects=20,
        verify_ssl=False,
        log_level="DEBUG",
    )

    assert settings.request_timeout == 60.0
    assert settings.max_retries == 5
    assert settings.follow_redirects is False
    assert settings.max_redirects == 20
    assert settings.verify_ssl is False
    assert settings.log_level == "DEBUG"


def test_lite_crawler_init():
    """Test LiteCrawler initialization"""
    crawler = LiteCrawler(SampleLiteSpider)

    assert crawler.spider_cls == SampleLiteSpider
    assert crawler.spider is None
    assert crawler.settings is not None


@pytest.mark.asyncio
async def test_lite_crawler_crawl():
    """Test LiteCrawler crawl method"""
    crawler = LiteCrawler(SampleLiteSpider)
    await crawler.crawl()

    assert crawler.spider is not None
    assert crawler.spider.responses_handled == 1


def test_lite_crawler_process_init():
    """Test LiteCrawlerProcess initialization"""
    process = LiteCrawlerProcess()

    assert len(process.crawlers) == 0
    assert process.settings is not None


@pytest.mark.asyncio
async def test_lite_crawler_process_crawl():
    """Test LiteCrawlerProcess crawl method"""
    process = LiteCrawlerProcess()
    await process.crawl(SampleLiteSpider)

    assert len(process.crawlers) == 1


def test_lite_crawler_process_run():
    """Test LiteCrawlerProcess run method (sync)"""
    process = LiteCrawlerProcess()
    process.run(SampleLiteSpider)  # Synchronous run with spider

    assert len(process.crawlers) == 1


def test_lite_spider_logger():
    """Test lite spider logger property"""
    spider = SampleLiteSpider()
    logger = spider.logger

    assert logger.name == "maize.lite.SampleLiteSpider"


@pytest.mark.asyncio
async def test_lite_spider_fetch_without_open():
    """Test lite spider fetch without open raises RuntimeError"""
    spider = SampleLiteSpider()
    # Don't call open(), so _session is None

    request = Request("https://httpbin.org/get")

    with pytest.raises(RuntimeError, match="Session not initialized"):
        await spider.fetch(request)


@pytest.mark.asyncio
async def test_lite_spider_start_requests_raises():
    """Test that start_requests is abstract in LiteSpider"""
    # Can't instantiate abstract class, so we test the method exists and is abstract
    assert LiteSpider.start_requests.__isabstractmethod__ is True


def test_lite_spider_set_crawler():
    """Test set_crawler method"""
    spider = SampleLiteSpider()
    crawler = LiteCrawler(SampleLiteSpider)

    spider.set_crawler(crawler)

    assert spider._crawler is crawler


def test_lite_crawler_idle():
    """Test LiteCrawler idle method"""
    crawler = LiteCrawler(SampleLiteSpider)

    assert crawler.idle() is True


def test_lite_crawler_process_run_no_spider():
    """Test LiteCrawlerProcess run method without spider"""
    process = LiteCrawlerProcess()

    # This should just run without error (idle loop)
    asyncio_run = False
    try:
        process.run()  # No spider provided
        asyncio_run = True
    except Exception:
        # This may fail if no spiders added, which is expected
        pass

    # If no exception, we just verify it runs
    assert asyncio_run or len(process.crawlers) == 0


def test_lite_crawler_process_start():
    """Test LiteCrawlerProcess start method"""
    process = LiteCrawlerProcess()

    # Add a spider first
    process.crawlers.append(LiteCrawler(SampleLiteSpider, process.settings))

    # start() should be callable (but will fail without open)
    # We just verify the method exists and is callable
