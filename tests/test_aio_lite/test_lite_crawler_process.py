"""
Tests for lite_crawler _process exception paths, semaphore, and coroutine parse.
"""

import asyncio
from unittest.mock import AsyncMock

import pytest

from maize.aio.lite.crawler.lite_crawler import LiteCrawler
from maize.aio.lite.spider.lite_spider import LiteSpider
from maize.common.http import Request, Response
from maize.common.items import Item


class _Spider(LiteSpider):
    async def start_requests(self):
        yield Request("https://example.com")

    async def parse(self, response: Response):
        pass


def _make_crawler(spider=None):
    spider = spider or _Spider()
    return LiteCrawler(spider, concurrency=1)


def _make_response(url="https://example.com", status=200):
    req = Request(url)
    return Response(url=url, headers={}, request=req, status=status, text="ok")


class TestProcessFetchException:
    """Cover _process fetch exception path (lines 213-220)."""

    @pytest.mark.asyncio
    async def test_fetch_exception_records_failed(self):
        spider = _Spider()
        await spider.open()
        spider.fetch = AsyncMock(side_effect=RuntimeError("connection reset"))
        crawler = _make_crawler(spider)

        queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        req = Request("https://example.com")
        req.meta["_lite_depth"] = 0
        await queue.put((0, 0, req))

        await crawler._process(req, queue)

        assert crawler.stats["failed"] == 1
        await spider.close()


class TestProcessParseException:
    """Cover _process parse exception path (lines 252-255)."""

    @pytest.mark.asyncio
    async def test_parse_exception_logged(self):
        spider = _Spider()
        await spider.open()
        spider.fetch = AsyncMock(return_value=_make_response())

        async def bad_parse(response):
            raise ValueError("parse error")

        spider.parse = bad_parse
        crawler = _make_crawler(spider)

        queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        req = Request("https://example.com")
        req.meta["_lite_depth"] = 0
        await queue.put((0, 0, req))

        await crawler._process(req, queue)
        # Should not raise; exception is caught and logged
        assert crawler.stats["succeeded"] == 1
        await spider.close()


class TestProcessCoroutineParse:
    """Cover _process coroutine parse path (line 251: `await result`)."""

    @pytest.mark.asyncio
    async def test_coroutine_parse_awaited(self):
        spider = _Spider()
        await spider.open()
        spider.fetch = AsyncMock(return_value=_make_response())

        async def coroutine_parse(response):
            pass

        spider.parse = coroutine_parse
        crawler = _make_crawler(spider)

        queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        req = Request("https://example.com")
        req.meta["_lite_depth"] = 0
        await queue.put((0, 0, req))

        await crawler._process(req, queue)
        # Should complete without error
        await spider.close()


class TestProcessProcessItemException:
    """Cover _process process_item exception path (lines 248-249)."""

    @pytest.mark.asyncio
    async def test_process_item_exception_logged(self):
        spider = _Spider()
        await spider.open()
        spider.fetch = AsyncMock(return_value=_make_response())

        async def parse_yielding_item(response):
            yield Item()

        spider.parse = parse_yielding_item
        spider.process_item = AsyncMock(side_effect=RuntimeError("db error"))
        crawler = _make_crawler(spider)

        queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        req = Request("https://example.com")
        req.meta["_lite_depth"] = 0
        await queue.put((0, 0, req))

        await crawler._process(req, queue)
        # Item still collected despite process_item error
        assert crawler.stats["items"] == 1
        await spider.close()


class TestProcessWithSemaphore:
    """Cover _process with per-domain semaphore (lines 206-209)."""

    @pytest.mark.asyncio
    async def test_process_with_semaphore(self):
        class SemSpider(_Spider):
            @property
            def per_domain_concurrency(self):
                return 1

        spider = SemSpider()
        await spider.open()
        spider.fetch = AsyncMock(return_value=_make_response())
        crawler = _make_crawler(spider)

        queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        req = Request("https://example.com")
        req.meta["_lite_depth"] = 0
        await queue.put((0, 0, req))

        await crawler._process(req, queue)
        assert crawler.stats["succeeded"] == 1
        await spider.close()
