from redis import asyncio as aioredis
from redis.typing import EncodableT, ExpiryT, KeyT

from .tools import SingletonType


class RedisUtil:
    def __init__(
        self,
        url: str | None = None,
        username: str | None = None,
        password: str | None = None,
        host: str | None = None,
        port: int | None = None,
        db: int | None = None,
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
        self._redis = aioredis.Redis(connection_pool=self._pool)

    async def open(self):
        """
        可以在此处进行一些异步初始化操作
        :return:
        """

    async def close(self):
        """
        关闭连接
        :return:
        """
        await self._redis.close()
        await self._pool.disconnect()

    async def set(
        self,
        name: KeyT,
        value: EncodableT,
        ex: ExpiryT | None = None,
        px: ExpiryT | None = None,
        nx: bool = False,
        xx: bool = False,
        keepttl: bool = False,
    ):
        """
        将关键字 `name` 的值设置为 `value`
        :param name:
        :param value:
        :param ex: 设置键 `name` 的过期标志为 `ex` 秒。
        :param px: 设置键 `name` 的过期标志，过期时间为 `px` 毫秒。
        :param nx: 如果设置为 True，则将键 `name` 的值设置为 `value`，前提是该值不存在。
        :param xx: 如果设置为 True，则将键 `name` 的值设置为 `value`，前提是该值已经存在。
        :param keepttl: 如果为 True，则保留与密钥相关的存活时间。
        :return:
        """
        return await self._redis.set(name=name, value=value, ex=ex, px=px, nx=nx, xx=xx, keepttl=keepttl)

    async def nx_set(
        self,
        name: KeyT,
        value: EncodableT,
        ex: ExpiryT | None = None,
    ):
        """
        nx set
        :param name:
        :param value:
        :param ex:
        @return:
        """
        result = await self._redis.set(name=name, value=value, nx=True, ex=ex)
        return bool(result)

    async def get(self, name: KeyT):
        """
        返回键 `name` 的值，如果键不存在，则返回 None
        :param name:
        :return:
        """
        return await self._redis.get(name)

    async def delete(self, *names: KeyT):
        """
        Delete one or more keys specified by ``names``
        :param names:
        @return:
        """
        return await self._redis.delete(*names)


class RedisSingletonUtil(RedisUtil, metaclass=SingletonType):
    """
    RedisUtil单例模式
    """
