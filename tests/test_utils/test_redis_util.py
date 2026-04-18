"""
Tests for redis_util
"""

from unittest.mock import AsyncMock, patch

import pytest

from maize.utils.redis_util import RedisUtil


class TestRedisUtil:
    """Test RedisUtil"""

    @pytest.fixture
    def mock_aioredis(self):
        """Create mock aioredis"""
        with patch("maize.utils.redis_util.aioredis") as mock:
            yield mock

    @pytest.fixture
    def redis_util(self, mock_aioredis):
        """Create RedisUtil instance"""
        return RedisUtil(
            url="redis://localhost:6379/0",
            username=None,
            password=None,
            host=None,
            port=None,
            db=None,
        )

    def test_init(self, redis_util, mock_aioredis):
        """Test __init__"""
        mock_aioredis.ConnectionPool.from_url.assert_called_once()
        mock_aioredis.Redis.assert_called_once()
        assert redis_util._redis is not None
        assert redis_util._pool is not None

    def test_init_with_host_port(self, mock_aioredis):
        """Test __init__ with host and port"""
        RedisUtil(
            url=None,
            username="user",
            password="pass",
            host="localhost",
            port=6379,
            db=1,
        )

        mock_aioredis.ConnectionPool.from_url.assert_called_once()
        mock_aioredis.Redis.assert_called_once()

    @pytest.mark.asyncio
    async def test_open(self, redis_util):
        """Test open - does nothing but should not raise"""
        await redis_util.open()

    @pytest.mark.asyncio
    async def test_close(self, redis_util, mock_aioredis):
        """Test close"""
        redis_util._redis.close = AsyncMock()
        redis_util._pool.disconnect = AsyncMock()

        await redis_util.close()

        redis_util._redis.close.assert_called_once()
        redis_util._pool.disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_set(self, redis_util, mock_aioredis):
        """Test set"""
        redis_util._redis.set = AsyncMock(return_value=True)

        result = await redis_util.set("key", "value", ex=100)

        assert result is True
        redis_util._redis.set.assert_called_once_with(
            name="key", value="value", ex=100, px=None, nx=False, xx=False, keepttl=False
        )

    @pytest.mark.asyncio
    async def test_set_with_all_params(self, redis_util, mock_aioredis):
        """Test set with all parameters"""
        redis_util._redis.set = AsyncMock(return_value=True)

        result = await redis_util.set(
            name="key",
            value="value",
            ex=100,
            px=200,
            nx=True,
            xx=False,
            keepttl=True,
        )

        assert result is True
        redis_util._redis.set.assert_called_once_with(
            name="key",
            value="value",
            ex=100,
            px=200,
            nx=True,
            xx=False,
            keepttl=True,
        )

    @pytest.mark.asyncio
    async def test_nx_set_success(self, redis_util, mock_aioredis):
        """Test nx_set when key doesn't exist"""
        redis_util._redis.set = AsyncMock(return_value=True)

        result = await redis_util.nx_set("key", "value", ex=100)

        assert result is True
        redis_util._redis.set.assert_called_once_with(name="key", value="value", nx=True, ex=100)

    @pytest.mark.asyncio
    async def test_nx_set_key_exists(self, redis_util, mock_aioredis):
        """Test nx_set when key already exists"""
        redis_util._redis.set = AsyncMock(return_value=None)

        result = await redis_util.nx_set("key", "value", ex=100)

        assert result is False

    @pytest.mark.asyncio
    async def test_get(self, redis_util, mock_aioredis):
        """Test get"""
        redis_util._redis.get = AsyncMock(return_value="value")

        result = await redis_util.get("key")

        assert result == "value"
        redis_util._redis.get.assert_called_once_with("key")

    @pytest.mark.asyncio
    async def test_get_key_not_exists(self, redis_util, mock_aioredis):
        """Test get when key doesn't exist"""
        redis_util._redis.get = AsyncMock(return_value=None)

        result = await redis_util.get("nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_delete(self, redis_util, mock_aioredis):
        """Test delete"""
        redis_util._redis.delete = AsyncMock(return_value=1)

        result = await redis_util.delete("key1", "key2")

        assert result == 1
        redis_util._redis.delete.assert_called_once_with("key1", "key2")

    @pytest.mark.asyncio
    async def test_delete_multiple_keys(self, redis_util, mock_aioredis):
        """Test delete with multiple keys"""
        redis_util._redis.delete = AsyncMock(return_value=3)

        result = await redis_util.delete("key1", "key2", "key3")

        assert result == 3
