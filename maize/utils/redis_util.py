from typing import Optional

import aioredis
from aioredis.client import ExpiryT
from aioredis.client import KeyT
from aioredis.connection import EncodableT

from maize.utils import SingletonType


class RedisUtil:
    def __init__(
        self,
        url: str = "redis://localhost",
        username: Optional[str] = None,
        password: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
        db: Optional[str] = None,
    ):
        """
        redis 工具类
        :param url: 可仅填 url，所有参数均可在 url 中设置。也可在 url 中忽略参数，设置到对应参数中。
        :param username:
        :param password:
        :param host:
        :param port:
        :param db:
        """
        self._pool = aioredis.ConnectionPool.from_url(
            url=url,
            username=username,
            password=password,
            host=host,
            port=port,
            db=db,
            encoding="utf-8",
            decode_responses=True,
        )
        self.redis = aioredis.Redis(connection_pool=self._pool)

    async def open(self):
        pass

    async def close(self):
        await self.redis.close()
        await self._pool.disconnect()

    async def set_data(
        self,
        name: KeyT,
        value: EncodableT,
        ex: Optional[ExpiryT] = None,
        px: Optional[ExpiryT] = None,
        nx: bool = False,
        xx: bool = False,
        keepttl: bool = False,
    ):
        return await self.redis.set(
            name=name, value=value, ex=ex, px=px, nx=nx, xx=xx, keepttl=keepttl
        )

    async def get_data(self, name: KeyT):
        return await self.redis.get(name)


class RedisSingletonUtil(RedisUtil, metaclass=SingletonType):
    """
    RedisUtil单例模式
    """
