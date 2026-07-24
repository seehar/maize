"""
MySQL 工具，基于 aiomysql 连接池提供异步数据库操作。
"""

from typing import Any, Union

import aiomysql

from .tools import SingletonType


class MysqlUtil:
    """
    MySQL 异步工具类，基于 aiomysql 连接池。

    :param host: 数据库主机地址
    :param db: 数据库名
    :param port: 端口，默认 3306
    :param user: 用户名，默认 "root"
    :param password: 密码，默认 ""
    :param minsize: 连接池最小连接数，默认 1
    :param maxsize: 连接池最大连接数，默认 10
    :param echo: 是否打印 SQL，默认 False
    :param pool_recycle: 连接回收时间（秒），-1 表示不回收，默认 -1
    """

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
        """
        初始化 MySQL 工具。

        :param host: 数据库主机地址
        :param db: 数据库名
        :param port: 端口，默认 3306
        :param user: 用户名，默认 "root"
        :param password: 密码，默认 ""
        :param minsize: 连接池最小连接数，默认 1
        :param maxsize: 连接池最大连接数，默认 10
        :param echo: 是否打印 SQL，默认 False
        :param pool_recycle: 连接回收时间（秒），-1 表示不回收，默认 -1
        """
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.db = db

        self.minsize = minsize
        self.maxsize = maxsize
        self.echo = echo
        self.pool_recycle = pool_recycle

        self.pool: aiomysql.Pool | None = None

    async def open(self):
        """
        打开数据库连接池。
        """
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

    async def fetchone(self, sql: str, args: Union[list, tuple] | None = None) -> dict[str, Any]:
        """
        查询单条数据
        :param sql: sql 语句
        :param args: list 或 tuple 类型的参数
        :return: 单条结果
        """
        async with self.pool.acquire() as conn, conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(sql, args)
            return await cur.fetchone()

    async def fetchall(self, sql: str, args: Union[list, tuple] | None = None) -> list[dict[str, Any]]:
        """
        查询多条数据
        :param sql: sql 语句
        :param args: list 或 tuple 类型的参数
        :return: 多条结果集
        """
        async with self.pool.acquire() as conn, conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(sql, args)
            return await cur.fetchall()

    async def execute(self, sql: str, args: Union[list, tuple] | None = None) -> int:
        """
        执行增删改操作
        :param sql: sql 语句
        :param args: list 或 tuple 类型的参数
        :return: 受影响的行数
        """
        async with self.pool.acquire() as conn, conn.cursor(aiomysql.DictCursor) as cur:
            try:
                row = await cur.execute(sql, args)
                await conn.commit()
                return row
            except Exception as e:
                await conn.rollback()
                raise e

    async def executemany(self, sql: str, args: Union[list, tuple] | None = None) -> int:
        """
        批量执行增删改操作
        :param sql: sql 语句
        :param args: ist 或 tuple 类型的参数
        :return: 受影响的行数
        """
        async with self.pool.acquire() as conn, conn.cursor(aiomysql.DictCursor) as cur:
            try:
                row = await cur.executemany(sql, args)
                await conn.commit()
                return row
            except Exception as e:
                await conn.rollback()
                raise e

    async def close(self):
        """
        关闭数据库连接池。
        """
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()
            self.pool = None


class MysqlSingletonUtil(MysqlUtil, metaclass=SingletonType):
    """
    MysqlUtil单例模式
    """
