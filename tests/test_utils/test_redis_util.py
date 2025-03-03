import pytest

from maize.utils.redis_util import RedisUtil


@pytest.skip(reason="redis test", allow_module_level=True)
@pytest.mark.asyncio
class TestRedisUtil:
    async def test_connection(self):
        redis_util = RedisUtil(
            url="redis://:123456@192.168.137.219:6379/0",
        )
        await redis_util.set("demo", 1)
        result = await redis_util.get("demo")
        assert result
        assert int(result) == 1

    async def test_nx_set(self):
        redis_util = RedisUtil(
            url="redis://:123456@192.168.137.219:6379/0",
        )
        for i in range(10):
            result = await redis_util.nx_set("demo", 1, 100)
            if i == 0:
                assert result

            else:
                assert not result
