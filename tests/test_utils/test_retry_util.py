from typing import Type

import pytest

from maize.exceptions import MaxRetryException
from maize.utils.retry_util import retry


@pytest.mark.asyncio
class TestRetryUtils:
    retry_max_count: int = 3
    retry_max_timeout: int = 1
    retry_catch_exc: Type[BaseException] = Exception
    retry_not_catch_exc: Type[BaseException] = ()

    @retry
    def error_func(self):
        return 1 / 0

    def test_retry_error(self):
        with pytest.raises(MaxRetryException):
            self.error_func()

    @retry
    async def async_error_func(self):
        return 1 / 0

    async def test_async_retry_error(self):
        with pytest.raises(MaxRetryException):
            await self.async_error_func()
