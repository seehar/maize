# RedisUtil

`RedisUtil` 是一个基于 `aioredis` 的异步 `Redis` 工具类，它提供了一些常用的 `Redis` 操作方法，
如 `set`、`get` 等。默认开启连接池。

## 单例模式

`ReidsSingletonUtil` 类实现了单例模式，使用方法与 `RedisUtil` 相同。

## 参数详解

| 参数名        | 类型              | 是否必须 | 默认值                 | 说明   |
|:-----------|:----------------|:-----|:--------------------|:-----|
| `url`      | `str`           | 是    | "redis://localhost" | 链接地址 |
| `username` | `Optional[str]` | 否    | `None`              | 用户名  |
| `password` | `Optional[str]` | 否    | `None`              | 密码   |
| `host`     | `Optional[str]` | 否    | `None`              | 链接地址 |
| `port`     | `Optional[int]` | 否    | `None`              | 端口   |
| `db`       | `Optional[str]` | 否    | `None`              | 数据库  |


## open

目前 open 中不进行任何操作，为了减少使用时的心智负担，与所有 `Util` 类一样，保留了异步 `open` 方法，
用户可以根据需要在此处进行一些异步初始化操作。

```python
async def open(self):
    """
    可以在此处进行一些异步初始化操作
    :return: 
    """
```


## close

```python
async def close(self):
    """
    关闭连接池
    :return: 
    """
```


## set

```python
async def set(
    self,
    name: KeyT,
    value: EncodableT,
    ex: Optional[ExpiryT] = None,
    px: Optional[ExpiryT] = None,
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
```


## get

```python
async def get(self, name: KeyT):
    """
    返回键 `name` 的值，如果键不存在，则返回 None
    :param name:
    :return:
    """
```
