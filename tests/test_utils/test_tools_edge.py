"""
Tests for tools retry return-None path (lines 30, 59).
"""

import pytest

from maize.utils.tools import retry, retry_asyncio


class TestRetryReturnNone:
    """Cover the unreachable `return None` path (lines 30, 59).

    The retry decorator loops range(retry_times) and raises on the last attempt.
    If retry_times=0, the loop never executes and falls through to `return None`.
    """

    def test_retry_zero_times_returns_none(self):
        call_count = 0

        @retry(retry_times=0, interval=0)
        def func():
            nonlocal call_count
            call_count += 1
            return "should not be called"

        assert func() is None
        assert call_count == 0


class TestRetryAsyncioReturnNone:
    """Cover the unreachable `return None` path (line 59)."""

    @pytest.mark.asyncio
    async def test_retry_asyncio_zero_times_returns_none(self):
        call_count = 0

        @retry_asyncio(retry_times=0, interval=0)
        async def func():
            nonlocal call_count
            call_count += 1
            return "should not be called"

        assert await func() is None
        assert call_count == 0
