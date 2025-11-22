# RedisUtil - Redis 工具类

## 简介

`RedisUtil` 是基于 `redis.asyncio` 的异步 Redis 工具类，提供了常用的 Redis 操作方法。它内置了连接池，支持高并发操作，适用于缓存、分布式锁、消息队列等场景。

### 主要特性

- ✅ **异步操作**：完全异步，不会阻塞事件循环
- ✅ **连接池管理**：自动管理 Redis 连接
- ✅ **简单易用**：封装了常用的 Redis 操作
- ✅ **单例模式**：支持单例模式，避免重复创建连接
- ✅ **灵活配置**：支持 URL 或单独参数配置
- ✅ **原生支持**：可以访问底层 Redis 客户端

## 安装依赖

```bash
pip install maize[redis]
# 或
pip install redis
```

## 基本使用

### 1. 创建实例

有两种方式创建 RedisUtil 实例：

**方式一：使用 URL**
```python
from maize.utils.redis_util import RedisUtil


# 使用 Redis URL
redis = RedisUtil(
    url="redis://username:password@localhost:6379/0"
)

await redis.open()
# ... 执行 Redis 操作 ...
await redis.close()
```

**方式二：使用独立参数**
```python
redis = RedisUtil(
    host="localhost",
    port=6379,
    db=0,
    username="default",      # 可选
    password="your_password" # 可选
)

await redis.open()
# ... 执行 Redis 操作 ...
await redis.close()
```

### 2. 使用单例模式

单例模式确保整个应用中只有一个 Redis 连接池实例：

```python
from maize.utils.redis_util import RedisSingletonUtil


# 第一次创建实例
redis = await RedisSingletonUtil.get_instance(
    host="localhost",
    port=6379,
    password="your_password"
)

# 后续获取同一个实例
redis2 = await RedisSingletonUtil.get_instance()
# redis 和 redis2 是同一个对象
```

## 构造参数

| 参数名        | 类型              | 默认值    | 说明                                                   |
|:-----------|:----------------|:-------|:-----------------------------------------------------|
| `url`      | `Optional[str]` | `None` | Redis URL（格式：redis://[[user]:password@]host:port/db） |
| `host`     | `Optional[str]` | `None` | Redis 服务器地址                                          |
| `port`     | `Optional[int]` | `None` | Redis 端口                                             |
| `db`       | `Optional[int]` | `None` | 数据库编号（0-15）                                          |
| `username` | `Optional[str]` | `None` | 用户名（Redis 6.0+）                                      |
| `password` | `Optional[str]` | `None` | 密码                                                   |

**注意：** `url` 参数的优先级高于独立参数。

## 核心方法

### open() - 初始化连接

初始化 Redis 连接。目前为空实现，保留用于未来扩展。

```python
await redis.open()
```

### close() - 关闭连接

关闭 Redis 连接池，释放所有连接。

```python
await redis.close()
```

### set() - 设置键值

设置键 `name` 的值为 `value`。

**参数：**
- `name` (str): 键名
- `value` (str | bytes): 值
- `ex` (Optional[int]): 过期时间（秒）
- `px` (Optional[int]): 过期时间（毫秒）
- `nx` (bool): 仅当键不存在时设置
- `xx` (bool): 仅当键存在时设置
- `keepttl` (bool): 保留键的 TTL

**示例：**
```python
# 基本设置
await redis.set("username", "alice")

# 设置带过期时间（10秒后过期）
await redis.set("session_id", "abc123", ex=10)

# 设置带过期时间（毫秒）
await redis.set("token", "xyz789", px=5000)  # 5秒后过期

# 仅当键不存在时设置（相当于 SETNX）
success = await redis.set("lock_key", "locked", nx=True)
if success:
    print("获取锁成功")

# 仅当键存在时更新
success = await redis.set("username", "bob", xx=True)
```

### nx_set() - 仅当键不存在时设置

`set()` 方法的便捷版本，等同于 `set(name, value, nx=True)`。

**参数：**
- `name` (str): 键名
- `value` (str | bytes): 值
- `ex` (Optional[int]): 过期时间（秒）

**示例：**
```python
# 分布式锁实现
lock_acquired = await redis.nx_set("my_lock", "locked", ex=10)
if lock_acquired:
    try:
        # 执行需要加锁的操作
        print("已获取锁，执行任务...")
    finally:
        await redis.delete("my_lock")
else:
    print("锁已被占用")
```

### get() - 获取值

获取键 `name` 的值，如果键不存在返回 `None`。

**参数：**
- `name` (str): 键名

**返回值：** `Optional[str]`

**示例：**
```python
# 获取值
username = await redis.get("username")
if username:
    print(f"用户名: {username}")
else:
    print("用户名不存在")

# 获取数字类型（需要转换）
count_str = await redis.get("visit_count")
if count_str:
    count = int(count_str)
    print(f"访问次数: {count}")
```

### delete() - 删除键

删除一个或多个键。

**参数：**
- `*names` (str): 一个或多个键名

**返回值：** `int` - 成功删除的键数量

**示例：**
```python
# 删除单个键
deleted = await redis.delete("session_id")
print(f"删除了 {deleted} 个键")

# 删除多个键
deleted = await redis.delete("key1", "key2", "key3")
print(f"删除了 {deleted} 个键")
```

## 高级操作

### 访问原生 Redis 客户端

RedisUtil 基于 `redis.asyncio.Redis`，您可以访问底层客户端使用所有 Redis 命令：

```python
# 获取底层客户端
client = redis.client

# 使用原生 Redis 命令

# 字符串操作
await client.incr("counter")           # 自增
await client.decr("counter")           # 自减
await client.append("key", "value")    # 追加

# 列表操作
await client.lpush("mylist", "item1", "item2")  # 左侧插入
await client.rpush("mylist", "item3")           # 右侧插入
await client.lrange("mylist", 0, -1)            # 获取列表

# 集合操作
await client.sadd("myset", "member1", "member2")  # 添加成员
await client.smembers("myset")                    # 获取所有成员
await client.sismember("myset", "member1")        # 检查成员

# 哈希操作
await client.hset("user:1", "name", "Alice")      # 设置字段
await client.hget("user:1", "name")               # 获取字段
await client.hgetall("user:1")                    # 获取所有字段

# 有序集合操作
await client.zadd("leaderboard", {"player1": 100, "player2": 200})
await client.zrange("leaderboard", 0, -1, withscores=True)

# 键操作
await client.exists("key")             # 检查键是否存在
await client.expire("key", 60)         # 设置过期时间
await client.ttl("key")                # 获取剩余时间
await client.keys("pattern*")          # 查找匹配的键
```

## 完整使用示例

### 示例1：在 Spider 中使用（缓存）

```python
import ujson
from typing import Any, AsyncGenerator

from maize import Request, Response, Spider, SpiderSettings
from maize.utils.redis_util import RedisUtil


class CacheSpider(Spider):
    def __init__(self):
        super().__init__()
        self.redis = None

    async def open(self, settings: SpiderSettings):
        """爬虫启动时初始化 Redis"""
        await super().open(settings)

        self.redis = RedisUtil(
            host=settings.redis.host,
            port=settings.redis.port,
            password=settings.redis.password,
            db=settings.redis.db
        )
        await self.redis.open()
        self.logger.info("Redis 连接已创建")

    async def close(self):
        """爬虫关闭时清理资源"""
        if self.redis:
            await self.redis.close()
            self.logger.info("Redis 连接已关闭")

        await super().close()

    async def start_requests(self) -> AsyncGenerator[Request, Any]:
        urls = [
            "http://example.com/page1",
            "http://example.com/page2",
            "http://example.com/page3",
        ]

        for url in urls:
            yield Request(url=url)

    async def parse(self, response: Response):
        # 尝试从缓存获取
        cache_key = f"page:{response.url}"
        cached_data = await self.redis.get(cache_key)

        if cached_data:
            self.logger.info(f"从缓存获取: {response.url}")
            data = ujson.loads(cached_data)
        else:
            self.logger.info(f"解析新页面: {response.url}")
            # 解析页面
            data = {
                'title': response.xpath('//title/text()').get(),
                'url': response.url
            }

            # 存入缓存（1小时过期）
            await self.redis.set(
                cache_key,
                ujson.dumps(data),
                ex=3600
            )

        yield data
```

### 示例2：分布式去重

```python
class DeduplicationSpider(Spider):
    def __init__(self):
        super().__init__()
        self.redis = None

    async def open(self, settings: SpiderSettings):
        await super().open(settings)
        self.redis = RedisUtil(url=settings.redis.url)
        await self.redis.open()

    async def close(self):
        if self.redis:
            await self.redis.close()
        await super().close()

    async def start_requests(self):
        yield Request(url="http://example.com")

    async def parse(self, response: Response):
        # 提取链接
        links = response.xpath('//a/@href').getall()

        for link in links:
            url = response.urljoin(link)

            # 使用 Redis 去重
            is_new = await self.redis.nx_set(f"visited:{url}", "1", ex=86400)

            if is_new:
                self.logger.info(f"新 URL: {url}")
                yield Request(url=url, callback=self.parse_detail)
            else:
                self.logger.debug(f"已访问: {url}")

    async def parse_detail(self, response: Response):
        # 处理详情页
        pass
```

### 示例3：分布式任务队列

```python
class TaskQueueSpider(Spider):
    def __init__(self):
        super().__init__()
        self.redis = None

    async def open(self, settings: SpiderSettings):
        await super().open(settings)
        self.redis = RedisUtil(url=settings.redis.url)
        await self.redis.open()

    async def start_requests(self):
        # 从 Redis 队列获取任务
        while True:
            # 从左侧弹出任务
            task = await self.redis.client.lpop("task_queue")

            if not task:
                self.logger.info("任务队列为空")
                break

            task_data = ujson.loads(task)
            yield Request(
                url=task_data['url'],
                meta={'task_id': task_data['id']}
            )

    async def parse(self, response: Response):
        task_id = response.meta['task_id']

        # 处理数据
        result = {
            'task_id': task_id,
            'title': response.xpath('//title/text()').get()
        }

        # 将结果推送到结果队列
        await self.redis.client.rpush(
            "result_queue",
            ujson.dumps(result)
        )

        # 标记任务完成
        await self.redis.set(f"task:{task_id}:status", "completed", ex=86400)

        yield result
```

### 示例4：分布式锁

```python
import asyncio


class DistributedLockExample:
    def __init__(self, redis: RedisUtil):
        self.redis = redis

    async def acquire_lock(self, lock_name: str, timeout: int = 10) -> bool:
        """获取分布式锁"""
        return await self.redis.nx_set(lock_name, "locked", ex=timeout)

    async def release_lock(self, lock_name: str):
        """释放分布式锁"""
        await self.redis.delete(lock_name)

    async def with_lock(self, lock_name: str):
        """使用分布式锁的上下文"""
        lock_acquired = await self.acquire_lock(lock_name)

        if not lock_acquired:
            print(f"无法获取锁: {lock_name}")
            return False

        try:
            # 执行需要加锁的操作
            print(f"已获取锁: {lock_name}")
            await asyncio.sleep(2)  # 模拟操作
            print("操作完成")
            return True
        finally:
            await self.release_lock(lock_name)
            print(f"已释放锁: {lock_name}")


# 使用示例
async def main():
    redis = RedisUtil(host="localhost", port=6379)
    await redis.open()

    lock_example = DistributedLockExample(redis)
    await lock_example.with_lock("my_resource_lock")

    await redis.close()
```

## 最佳实践

### 1. 使用单例模式

在多个组件中共享 Redis 连接：

```python
# 在 Spider 中
redis = await RedisSingletonUtil.get_instance(url=settings.redis.url)

# 在 Pipeline 中
redis = await RedisSingletonUtil.get_instance()  # 获取同一个实例
```

### 2. 设置合理的过期时间

```python
# 短期缓存（5分钟）
await redis.set("temp_data", value, ex=300)

# 中期缓存（1小时）
await redis.set("session_data", value, ex=3600)

# 长期缓存（1天）
await redis.set("config_data", value, ex=86400)
```

### 3. 使用命名空间

使用前缀避免键名冲突：

```python
# 不推荐
await redis.set("user_1", data)

# 推荐：使用命名空间
await redis.set("spider:user:1", data)
await redis.set("spider:cache:page:1", data)
```

### 4. 批量操作

使用 pipeline 提高性能：

```python
# 使用 pipeline 批量操作
pipe = redis.client.pipeline()
for i in range(100):
    pipe.set(f"key_{i}", f"value_{i}")
await pipe.execute()
```

### 5. 错误处理

```python
try:
    value = await redis.get("key")
    if value:
        print(value)
except Exception as e:
    logger.error(f"Redis 操作失败: {e}")
    # 降级处理或重试
```

## 常见问题

### 1. 如何在配置中设置 Redis？

```python
# settings.py
from maize import SpiderSettings


class Settings(SpiderSettings):
    pass


settings = Settings()
settings.redis.host = "localhost"
settings.redis.port = 6379
settings.redis.password = "your_password"
settings.redis.db = 0
```

### 2. 如何生成 Redis URL？

```python
# 通过 settings 自动生成
redis_url = settings.redis.url
# 结果：redis://localhost:6379/0

# 或手动拼接
redis_url = f"redis://{username}:{password}@{host}:{port}/{db}"
```

### 3. 如何处理连接失败？

```python
try:
    redis = RedisUtil(host="localhost", port=6379)
    await redis.open()
    # 测试连接
    await redis.client.ping()
except Exception as e:
    logger.error(f"Redis 连接失败: {e}")
    # 降级处理
```

### 4. 如何序列化复杂对象？

```python
import ujson

# 存储
data = {'name': 'Alice', 'age': 25, 'tags': ['python', '爬虫']}
await redis.set("user:1", ujson.dumps(data))

# 读取
value = await redis.get("user:1")
if value:
    data = ujson.loads(value)
```

## 注意事项

1. **记得关闭连接**：程序结束时调用 `close()` 释放连接
2. **使用过期时间**：避免 Redis 内存占用过高
3. **避免大 key**：单个 key 的值不要太大（建议 < 10MB）
4. **使用命名空间**：使用有意义的前缀组织键名
5. **谨慎使用 keys**：生产环境避免使用 `keys *`，改用 `scan`

## 下一步

- [MysqlUtil](mysql_util.md) - MySQL 工具类使用
- [配置说明](settings.md) - Redis 配置选项
- [Spider 进阶](spider.md) - 在爬虫中使用 Redis
