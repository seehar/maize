import pytest

from maize.utils.tools import SingletonType, retry, retry_asyncio


class Demo:
    def __init__(self):
        self.count = None

    async def open(self):
        self.count = 0

    async def close(self):
        self.count = None


class Singleton(Demo, metaclass=SingletonType):
    pass


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

    async def test_singleton_type(self):
        cls_1: Singleton = Singleton()
        cls_2 = Singleton()

        await cls_1.open()
        assert cls_1.count == 0
        assert cls_2.count == 0

        await cls_2.close()
        assert cls_1.count is None
        assert cls_2.count is None
