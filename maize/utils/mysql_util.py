import typing

import aiomysql

from .tools import SingletonType


class MysqlUtil:
    def __init__(
        self,
        host: str,
        db: str,
        port: int = 3306,
        user: str = "root",
        password: str = "",
        minsize: int = 1,
        maxsize: int = 10,
        echo: bool = False,
        pool_recycle: int = -1,
    ):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.db = db

        self.minsize = minsize
        self.maxsize = maxsize
        self.echo = echo
        self.pool_recycle = pool_recycle

        self.pool: typing.Optional[aiomysql.Pool] = None

    async def open(self):
        if self.pool:
            return

        self.pool = await aiomysql.create_pool(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            db=self.db,
            minsize=self.minsize,
            maxsize=self.maxsize,
            echo=self.echo,
            pool_recycle=self.pool_recycle,
        )

    async def fetchone(
        self, sql: str, args: typing.Optional[list | set] = None
    ) -> dict[str, typing.Any]:
        """
        查询单条数据
        :param sql: sql 语句
        :param args: list 或 set 类型的参数
        :return: 单条结果
        """
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(sql, args)
                return await cur.fetchone()

    async def fetchall(
        self, sql: str, args: typing.Optional[list | set] = None
    ) -> list[dict[str, typing.Any]]:
        """
        查询多条数据
        :param sql: sql 语句
        :param args: list 或 set 类型的参数
        :return: 多条结果集
        """
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(sql, args)
                return await cur.fetchall()

    async def execute(self, sql: str, args: typing.Optional[list | set] = None):
        """
        执行增删改操作
        :param sql: sql 语句
        :param args: list 或 set 类型的参数
        :return: 无返回
        """
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                try:
                    await cur.execute(sql, args)
                    await conn.commit()
                except Exception as e:
                    await conn.rollback()
                    raise e

    async def executemany(self, sql: str, args: typing.Optional[list | set] = None):
        """
        批量执行增删改操作
        :param sql: sql 语句
        :param args: ist 或 set 类型的参数
        :return: 无返回
        """
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                try:
                    await cur.executemany(sql, args)
                    await conn.commit()
                except Exception as e:
                    await conn.rollback()
                    raise e

    async def close(self):
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()
            self.pool = None


class MysqlSingletonUtil(MysqlUtil, metaclass=SingletonType):
    """
    MysqlUtil单例模式
    """
