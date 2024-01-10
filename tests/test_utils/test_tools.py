import pytest

from maize.utils.tools import retry
from maize.utils.tools import retry_asyncio


@pytest.mark.asyncio
class TestTools:
    @retry()
    def retry_demo(self):
        return 1 / 0

    def test_retry(self):
        with pytest.raises(ZeroDivisionError):
            self.retry_demo()

    @retry_asyncio()
    async def async_retry_demo(self):
        return 1 / 0

    async def test_async_retry_demo(self):
        with pytest.raises(ZeroDivisionError):
            await self.async_retry_demo()
