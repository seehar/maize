"""
Tests for lite_spider fetch exception path, run, and _run.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from maize.aio.lite.spider.lite_spider import LiteSpider
from maize.common.http import Request, Response


class FetchErrorSpider(LiteSpider):
    """Spider whose fetch always raises."""

    async def start_requests(self):
        yield Request("https://example.com")

    async def parse(self, response: Response):
        pass


class TestLiteSpiderFetchException:
    """Test LiteSpider.fetch exception handling."""

    @pytest.mark.asyncio
    async def test_fetch_returns_status_0_on_exception(self):
        spider = FetchErrorSpider()
        await spider.open()

        # Mock session.request to raise
        spider._session = MagicMock()
        spider._session.request = MagicMock(side_effect=RuntimeError("connection refused"))

        req = Request("https://example.com")
        response = await spider.fetch(req)

        assert response.status == 0
        assert response.body == b""
        spider._session = None  # avoid await on MagicMock in close()
        await spider.close()

    @pytest.mark.asyncio
    async def test_fetch_returns_response_on_success(self):
        spider = FetchErrorSpider()
        await spider.open()

        mock_response = MagicMock()
        mock_response.url = "https://example.com"
        mock_response.headers = {"Content-Type": "text/html"}
        mock_response.status = 200
        mock_response.read = AsyncMock(return_value=b"<html>ok</html>")

        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_response)
        mock_ctx.__aexit__ = AsyncMock(return_value=None)

        spider._session = MagicMock()
        spider._session.request = MagicMock(return_value=mock_ctx)

        req = Request("https://example.com")
        response = await spider.fetch(req)

        assert response.status == 200
        assert response.body == b"<html>ok</html>"
        assert response.url == "https://example.com"
        spider._session = None
        await spider.close()


class TestLiteSpiderRun:
    """Test LiteSpider.run and _run."""

    def test_run_calls_asyncio_run(self):
        spider = FetchErrorSpider()
        with patch("maize.aio.lite.spider.lite_spider.asyncio.run") as mock_run:
            spider.run()
            mock_run.assert_called_once()

    def test_run_handles_keyboard_interrupt(self):
        spider = FetchErrorSpider()
        with patch("maize.aio.lite.spider.lite_spider.asyncio.run", side_effect=KeyboardInterrupt):
            # Should not raise
            spider.run()

    @pytest.mark.asyncio
    async def test_run_creates_crawler(self):
        spider = FetchErrorSpider()
        with patch("maize.aio.lite.spider.lite_spider.LiteCrawler") as mock_crawler_cls:
            mock_crawler = MagicMock()
            mock_crawler.crawl = AsyncMock()
            mock_crawler_cls.return_value = mock_crawler

            await spider._run()
            mock_crawler_cls.assert_called_once()
            mock_crawler.crawl.assert_called_once()


class TestLiteSpiderShouldRetry:
    """Test LiteSpider.should_retry edge cases."""

    def test_retry_on_503(self):
        spider = FetchErrorSpider()
        resp = MagicMock()
        resp.status = 503
        assert spider.should_retry(resp) is True

    def test_retry_on_502(self):
        spider = FetchErrorSpider()
        resp = MagicMock()
        resp.status = 502
        assert spider.should_retry(resp) is True

    def test_no_retry_on_301(self):
        spider = FetchErrorSpider()
        resp = MagicMock()
        resp.status = 301
        assert spider.should_retry(resp) is False

    def test_no_retry_on_200(self):
        spider = FetchErrorSpider()
        resp = MagicMock()
        resp.status = 200
        assert spider.should_retry(resp) is False


class TestLiteSpiderProcessItem:
    """Test LiteSpider.process_item hook."""

    @pytest.mark.asyncio
    async def test_process_item_default_noop(self):
        spider = FetchErrorSpider()
        item = MagicMock()
        # Default implementation should not raise
        await spider.process_item(item)


class TestLiteSpiderOnStartOnClose:
    """Test LiteSpider on_start/on_close hooks."""

    @pytest.mark.asyncio
    async def test_on_start_default_noop(self):
        spider = FetchErrorSpider()
        await spider.on_start()

    @pytest.mark.asyncio
    async def test_on_close_default_noop(self):
        spider = FetchErrorSpider()
        await spider.on_close()
