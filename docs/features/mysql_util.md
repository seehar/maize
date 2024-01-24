# MysqlUtil

`MysqlUtil` 是一个基于 `aiomysql` 的异步 MySQL 工具类，它提供了一些常用的数据库操作方法，内置连接池，支持多线程并发操作。

## 单例模式

`MysqlSingletonUtil` 类实现了单例模式，使用方法与 `MysqlUtil` 相同。

## 参数详解

| 参数名            | 类型     | 是否必须 | 默认值     | 说明       |
|:---------------|:-------|:-----|:--------|:---------|
| `host`         | `str`  | 是    |         | 数据库地址    |
| `port`         | `int`  | 否    | 3306    | 数据库端口    |
| `user`         | `str`  | 否    | root    | 数据库用户名   |
| `password`     | `str`  | 是    |         | 数据库密码    |
| `db`           | `str`  | 是    |         | 数据库名     |
| `minsize`      | `int`  | 否    | 1       | 连接池最小连接数 |
| `maxsize`      | `int`  | 否    | 10      | 连接池最大连接数 |
| `echo`         | `bool` | 否    | `False` |          |
| `pool_recycle` | `int`  | 否    | `-1`    |          |


## open

开启连接池，如果已经开启则不会重复开启

## close

关闭连接池，如果已经关闭则不会重复关闭

## fetchone

```python
async def fetchone(
    self, sql: str, args: typing.Optional[list | set] = None
) -> dict[str, typing.Any]:
    """
    查询单条数据
    :param sql: sql 语句
    :param args: list 或 set 类型的参数
    :return: 单条结果集
    """
```

## fetchall

```python
async def fetchall(
    self, sql: str, args: typing.Optional[list | set] = None
) -> list[dict[str, typing.Any]]:
    """
    查询多条数据
    :param sql: sql 语句
    :param args: list 或 set 类型的参数
    :return: 多条结果集
    """
```

## execute

```python
async def execute(self, sql: str, args: typing.Optional[list | set] = None):
    """
    执行增删改操作
    :param sql: sql 语句
    :param args: list 或 set 类型的参数
    :return: 无返回
    """
```

## executemany

```python
async def executemany(self, sql: str, args: typing.Optional[list | set] = None):
    """
    批量执行增删改操作
    :param sql: sql 语句
    :param args: ist 或 set 类型的参数
    :return: 无返回
    """
```
