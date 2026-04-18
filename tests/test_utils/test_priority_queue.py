"""
Tests for priority_queue
"""

import pytest

from maize.utils.priority_queue import SpiderPriorityQueue


class MockItem:
    """Mock item with priority - comparable for heapq"""

    def __init__(self, value, priority=0):
        self.value = value
        self.priority = priority

    def __lt__(self, other):
        return self.priority < other.priority

    def __le__(self, other):
        return self.priority <= other.priority

    def __hash__(self):
        return hash((self.value, self.priority))

    def __gt__(self, other):
        return self.priority > other.priority

    def __ge__(self, other):
        return self.priority >= other.priority

    def __eq__(self, other):
        return self.priority == other.priority


class TestSpiderPriorityQueue:
    """Test SpiderPriorityQueue"""

    @pytest.fixture
    def queue(self):
        """Create SpiderPriorityQueue"""
        return SpiderPriorityQueue(maxsize=10)

    @pytest.mark.asyncio
    async def test_put_and_get(self, queue):
        """Test basic put and get"""
        item = MockItem("test", priority=5)
        await queue.put(item)

        result = await queue.get()

        assert result.value == "test"
        assert result.priority == 5

    @pytest.mark.asyncio
    async def test_get_empty_queue_returns_none(self, queue):
        """Test that get returns None when queue is empty after timeout"""
        result = await queue.get()

        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_priority_finds_item(self, queue):
        """Test get_by_priority finds item with matching priority"""
        item = MockItem("test", priority=5)
        await queue.put(item)

        result = await queue.get_by_priority(gte_priority=4)

        assert result is not None
        assert result.value == "test"
        assert result.priority == 5

    @pytest.mark.asyncio
    async def test_get_by_priority_returns_none_when_empty(self, queue):
        """Test get_by_priority returns None when queue is empty"""
        result = await queue.get_by_priority(gte_priority=0)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_priority_returns_none_when_priority_too_high(self, queue):
        """Test get_by_priority returns None when item priority is too low"""
        item = MockItem("test", priority=3)
        await queue.put(item)

        result = await queue.get_by_priority(gte_priority=5)

        assert result is None
        # Item should be put back
        item_back = await queue.get()
        assert item_back is not None
        assert item_back.priority == 3

    @pytest.mark.asyncio
    async def test_get_by_priority_equal_boundary(self, queue):
        """Test get_by_priority with exact priority match"""
        item = MockItem("test", priority=5)
        await queue.put(item)

        result = await queue.get_by_priority(gte_priority=5)

        assert result is not None
        assert result.priority == 5

    @pytest.mark.asyncio
    async def test_maxsize(self):
        """Test queue respects maxsize"""
        queue = SpiderPriorityQueue(maxsize=2)
        await queue.put(MockItem("1"))
        await queue.put(MockItem("2"))

        # Queue should be full
        assert queue.full()
