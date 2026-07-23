"""
Tests for utils.tools: retry, retry_asyncio, SingletonType.
"""

import threading
from unittest.mock import patch

import pytest

from maize.utils.tools import SingletonType, retry, retry_asyncio


class TestRetry:
    """Test the sync retry decorator."""

    def test_success_first_try(self):
        call_count = 0

        @retry(retry_times=3, interval=0)
        def func():
            nonlocal call_count
            call_count += 1
            return "ok"

        assert func() == "ok"
        assert call_count == 1

    def test_retries_on_failure_then_succeeds(self):
        call_count = 0

        @retry(retry_times=3, interval=0)
        def func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("fail")
            return "recovered"

        assert func() == "recovered"
        assert call_count == 3

    def test_raises_after_exhausting_retries(self):
        call_count = 0

        @retry(retry_times=2, interval=0)
        def func():
            nonlocal call_count
            call_count += 1
            raise ValueError("always fail")

        with pytest.raises(ValueError, match="always fail"):
            func()
        assert call_count == 2

    def test_preserves_function_name(self):
        @retry()
        def my_function():
            """docstring"""

        assert my_function.__name__ == "my_function"
        assert my_function.__doc__ == "docstring"

    def test_default_retry_times_is_3(self):
        call_count = 0

        @retry(interval=0)
        def func():
            nonlocal call_count
            call_count += 1
            raise RuntimeError("boom")

        with pytest.raises(RuntimeError):
            func()
        assert call_count == 3

    @patch("maize.utils.tools.time.sleep")
    def test_interval_applied_between_retries(self, mock_sleep):
        call_count = 0

        @retry(retry_times=3, interval=2)
        def func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("fail")
            return "ok"

        assert func() == "ok"
        # 2 retries means 2 sleeps of 2 seconds each
        assert mock_sleep.call_count == 2
        mock_sleep.assert_called_with(2)

    @patch("maize.utils.tools.logging.error")
    def test_logs_error_on_each_failure(self, mock_log_error):
        @retry(retry_times=2, interval=0)
        def func():
            raise ValueError("logged error")

        with pytest.raises(ValueError):
            func()
        assert mock_log_error.call_count == 2


class TestRetryAsyncio:
    """Test the async retry decorator."""

    @pytest.mark.asyncio
    async def test_success_first_try(self):
        call_count = 0

        @retry_asyncio(retry_times=3, interval=0)
        async def func():
            nonlocal call_count
            call_count += 1
            return "ok"

        assert await func() == "ok"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retries_on_failure_then_succeeds(self):
        call_count = 0

        @retry_asyncio(retry_times=3, interval=0)
        async def func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("fail")
            return "recovered"

        assert await func() == "recovered"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_raises_after_exhausting_retries(self):
        call_count = 0

        @retry_asyncio(retry_times=2, interval=0)
        async def func():
            nonlocal call_count
            call_count += 1
            raise ValueError("always fail")

        with pytest.raises(ValueError, match="always fail"):
            await func()
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_preserves_function_name(self):
        @retry_asyncio()
        async def my_async_func():
            """async docstring"""

        assert my_async_func.__name__ == "my_async_func"
        assert my_async_func.__doc__ == "async docstring"

    @pytest.mark.asyncio
    @patch("maize.utils.tools.asyncio.sleep")
    async def test_interval_applied_between_retries(self, mock_sleep):
        call_count = 0

        @retry_asyncio(retry_times=3, interval=2)
        async def func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("fail")
            return "ok"

        assert await func() == "ok"
        assert mock_sleep.call_count == 2


class TestSingletonType:
    """Test the SingletonType metaclass."""

    def test_single_instance(self):
        class Single(metaclass=SingletonType):
            def __init__(self):
                self.value = 0

        a = Single()
        b = Single()
        assert a is b

        a.value = 42
        assert b.value == 42

    def test_singleton_init_runs_once(self):
        """__init__ only runs on first instantiation; later calls return cached instance."""

        class Config(metaclass=SingletonType):
            def __init__(self, name="default"):
                self.name = name

        a = Config(name="first")
        b = Config(name="second")
        assert a is b
        assert a.name == "first"
        assert b.name == "first"

    def test_singleton_thread_safety(self):
        """SingletonType uses an RLock; verify it doesn't deadlock under concurrent access."""

        class Shared(metaclass=SingletonType):
            pass

        instances = []

        def create():
            instances.append(Shared())

        threads = [threading.Thread(target=create) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(instances) == 5
        assert all(inst is instances[0] for inst in instances)
