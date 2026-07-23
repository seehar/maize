"""
Tests for classic Scheduler.
"""

import pytest

from maize.aio.classic.scheduler.scheduler import Scheduler
from maize.common.http.request import Request


class TestScheduler:
    """Test Scheduler queue operations."""

    def test_init(self):
        scheduler = Scheduler()
        assert scheduler.request_queue is None
        assert len(scheduler) == 0
        assert scheduler.idle() is True

    def test_open_creates_queue(self):
        scheduler = Scheduler()
        scheduler.open()
        assert scheduler.request_queue is not None

    def test_idle_when_empty(self):
        scheduler = Scheduler()
        scheduler.open()
        assert scheduler.idle() is True

    @pytest.mark.asyncio
    async def test_enqueue_and_next_request(self):
        scheduler = Scheduler()
        scheduler.open()
        req = Request("https://example.com")
        await scheduler.enqueue_request(req)
        assert len(scheduler) == 1
        assert not scheduler.idle()

        result = await scheduler.next_request()
        assert result is req
        assert scheduler.idle()

    @pytest.mark.asyncio
    async def test_next_request_empty_returns_none(self):
        scheduler = Scheduler()
        scheduler.open()
        result = await scheduler.next_request()
        assert result is None

    @pytest.mark.asyncio
    async def test_next_request_without_open(self):
        """next_request before open() should raise AttributeError on None queue."""
        scheduler = Scheduler()
        with pytest.raises(AttributeError):
            await scheduler.next_request()

    @pytest.mark.asyncio
    async def test_priority_ordering(self):
        """Scheduler respects Request.__lt__ (min-heap: smaller priority first)."""
        scheduler = Scheduler()
        scheduler.open()

        low = Request("https://low.com", priority=10)
        high = Request("https://high.com", priority=1)
        mid = Request("https://mid.com", priority=5)

        await scheduler.enqueue_request(low)
        await scheduler.enqueue_request(mid)
        await scheduler.enqueue_request(high)

        first = await scheduler.next_request()
        second = await scheduler.next_request()
        third = await scheduler.next_request()

        assert first.priority == 1
        assert second.priority == 5
        assert third.priority == 10

    @pytest.mark.asyncio
    async def test_next_request_with_gte_priority(self):
        """next_request(gte_priority) only returns items >= priority.

        get_by_priority peeks at the min-heap head (lowest priority first).
        If the head doesn't meet gte_priority, it's requeued and None returned.
        """
        scheduler = Scheduler()
        scheduler.open()

        req_low = Request("https://low.com", priority=1)
        req_high = Request("https://high.com", priority=10)

        await scheduler.enqueue_request(req_low)
        await scheduler.enqueue_request(req_high)

        # gte_priority=5: head is low (1 < 5), requeued, returns None
        result = await scheduler.next_request(gte_priority=5)
        assert result is None
        # Both items still in queue
        assert not scheduler.idle()

        # Without gte_priority, low (priority=1) comes out first
        result = await scheduler.next_request()
        assert result is req_low

    @pytest.mark.asyncio
    async def test_next_request_with_gte_priority_none_matching(self):
        """next_request(gte_priority) returns None when no item matches."""
        scheduler = Scheduler()
        scheduler.open()

        req = Request("https://low.com", priority=1)
        await scheduler.enqueue_request(req)

        result = await scheduler.next_request(gte_priority=100)
        assert result is None
        # Item requeued since it didn't match
        assert not scheduler.idle()
