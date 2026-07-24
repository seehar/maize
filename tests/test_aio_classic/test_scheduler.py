"""
Tests for SpiderPriorityQueue (async).
"""

import pytest

from maize.aio.classic.scheduler import SpiderPriorityQueue
from maize.common.http.request import Request


class TestSpiderPriorityQueue:
    """Test SpiderPriorityQueue queue operations."""

    def test_init(self):
        queue = SpiderPriorityQueue()
        assert queue.qsize() == 0

    def test_idle_when_empty(self):
        queue = SpiderPriorityQueue()
        assert queue.qsize() == 0

    @pytest.mark.asyncio
    async def test_enqueue_and_next_request(self):
        queue = SpiderPriorityQueue()
        req = Request("https://example.com")
        await queue.put(req)
        result = await queue.get()
        assert result is req
        assert queue.qsize() == 0

    @pytest.mark.asyncio
    async def test_next_request_empty_returns_none(self):
        queue = SpiderPriorityQueue()
        result = await queue.get()
        assert result is None

    @pytest.mark.asyncio
    async def test_priority_ordering(self):
        """Queue respects Request.__lt__ (min-heap: smaller priority first)."""
        queue = SpiderPriorityQueue()

        low = Request("https://low.com", priority=10)
        high = Request("https://high.com", priority=1)
        mid = Request("https://mid.com", priority=5)

        await queue.put(low)
        await queue.put(high)
        await queue.put(mid)

        first = await queue.get()
        second = await queue.get()
        third = await queue.get()

        assert first.priority == 1
        assert second.priority == 5
        assert third.priority == 10

    @pytest.mark.asyncio
    async def test_next_request_with_gte_priority(self):
        """get_by_priority returns the head item if it meets the threshold.

        Min-heap: priority 1 is highest (head). get_by_priority(1) returns
        req_low because 1 >= 1. Does NOT iterate past the head.
        """
        queue = SpiderPriorityQueue()

        req_low = Request("https://low.com", priority=1)
        req_high = Request("https://high.com", priority=10)

        await queue.put(req_low)
        await queue.put(req_high)

        result = await queue.get_by_priority(1)
        assert result is req_low
        assert result.priority >= 1

    @pytest.mark.asyncio
    async def test_next_request_with_gte_priority_none_matching(self):
        """get_by_priority returns None when no item matches, and re-queues non-matching."""
        queue = SpiderPriorityQueue()

        req = Request("https://low.com", priority=1)
        await queue.put(req)

        result = await queue.get_by_priority(10)
        assert result is None
        # Non-matching item was put back
        assert queue.qsize() > 0
