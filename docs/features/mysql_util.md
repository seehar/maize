# MysqlUtil - MySQL 工具类

## 简介

`MysqlUtil` 是基于 `aiomysql` 的异步 MySQL 工具类，提供了常用的数据库操作方法。它内置了连接池，支持高并发操作，是 maize 框架推荐的 MySQL 操作方式。

### 主要特性

- ✅ **异步操作**：完全异步，不会阻塞事件循环
- ✅ **连接池管理**：自动管理数据库连接，提高性能
- ✅ **简单易用**：封装了常用的 CRUD 操作
- ✅ **单例模式**：支持单例模式，避免重复创建连接
- ✅ **参数化查询**：防止 SQL 注入
- ✅ **批量操作**：支持批量插入、更新等操作

## 安装依赖

```bash
pip install maize[mysql]
# 或
pip install aiomysql
```

## 基本使用

### 1. 创建实例

```python
from maize.utils.mysql_util import MysqlUtil


# 创建 MySQL 工具实例
mysql = MysqlUtil(
    host="localhost",
    port=3306,
    user="root",
    password="your_password",
    db="your_database"
)

# 开启连接池
await mysql.open()

# ... 执行数据库操作 ...

# 关闭连接池
await mysql.close()
```

### 2. 使用单例模式

单例模式确保整个应用中只有一个数据库连接池实例：

```python
from maize.utils.mysql_util import MysqlSingletonUtil


# 第一次创建实例
mysql = await MysqlSingletonUtil.get_instance(
    host="localhost",
    port=3306,
    user="root",
    password="your_password",
    db="your_database"
)

# 后续获取同一个实例
mysql2 = await MysqlSingletonUtil.get_instance()
# mysql 和 mysql2 是同一个对象
```

## 构造参数

| 参数名            | 类型     | 默认值       | 说明                   |
|:---------------|:-------|:----------|:---------------------|
| `host`         | `str`  | -         | MySQL 服务器地址          |
| `port`         | `int`  | `3306`    | MySQL 端口             |
| `user`         | `str`  | `root`    | 数据库用户名               |
| `password`     | `str`  | -         | 数据库密码                |
| `db`           | `str`  | -         | 数据库名称                |
| `minsize`      | `int`  | `1`       | 连接池最小连接数             |
| `maxsize`      | `int`  | `10`      | 连接池最大连接数             |
| `echo`         | `bool` | `False`   | 是否打印 SQL 语句          |
| `pool_recycle` | `int`  | `-1`      | 连接回收时间（秒），-1 表示不自动回收 |
| `charset`      | `str`  | `utf8mb4` | 字符集                  |

## 核心方法

### open() - 开启连接池

初始化并开启数据库连接池。如果连接池已经开启，不会重复开启。

```python
await mysql.open()
```

### close() - 关闭连接池

关闭数据库连接池，释放所有连接。如果连接池已经关闭，不会重复关闭。

```python
await mysql.close()
```

### fetchone() - 查询单条数据

查询并返回单条记录。

**参数：**
- `sql` (str): SQL 查询语句
- `args` (Optional[list | tuple]): 参数化查询的参数

**返回值：** `dict[str, Any]` - 单条记录的字典

**示例：**
```python
# 不带参数的查询
result = await mysql.fetchone("SELECT * FROM users LIMIT 1")
print(result)  # {'id': 1, 'name': 'Alice', 'age': 25}

# 参数化查询
user = await mysql.fetchone(
    "SELECT * FROM users WHERE id = %s",
    args=(1,)
)
print(user['name'])  # Alice

# 使用命名参数
user = await mysql.fetchone(
    "SELECT * FROM users WHERE name = %(name)s",
    args={'name': 'Alice'}
)
```

### fetchall() - 查询多条数据

查询并返回所有匹配的记录。

**参数：**
- `sql` (str): SQL 查询语句
- `args` (Optional[list | tuple]): 参数化查询的参数

**返回值：** `list[dict[str, Any]]` - 记录列表

**示例：**
```python
# 查询所有用户
users = await mysql.fetchall("SELECT * FROM users")
for user in users:
    print(f"{user['id']}: {user['name']}")

# 带条件的查询
active_users = await mysql.fetchall(
    "SELECT * FROM users WHERE status = %s",
    args=('active',)
)

# 分页查询
page_users = await mysql.fetchall(
    "SELECT * FROM users LIMIT %s OFFSET %s",
    args=(10, 0)  # 每页10条，第1页
)
```

### execute() - 执行增删改操作

执行 INSERT、UPDATE、DELETE 等操作。

**参数：**
- `sql` (str): SQL 语句
- `args` (Optional[list | tuple]): 参数化查询的参数

**返回值：** `int` - 受影响的行数

**示例：**
```python
# 插入数据
rows = await mysql.execute(
    "INSERT INTO users (name, age, email) VALUES (%s, %s, %s)",
    args=('Bob', 30, 'bob@example.com')
)
print(f"插入了 {rows} 行")

# 更新数据
rows = await mysql.execute(
    "UPDATE users SET age = %s WHERE name = %s",
    args=(31, 'Bob')
)
print(f"更新了 {rows} 行")

# 删除数据
rows = await mysql.execute(
    "DELETE FROM users WHERE age > %s",
    args=(100,)
)
print(f"删除了 {rows} 行")
```

### executemany() - 批量执行操作

批量执行 INSERT、UPDATE、DELETE 等操作，比多次调用 execute() 更高效。

**参数：**
- `sql` (str): SQL 语句
- `args` (Optional[list[tuple]]): 参数列表

**返回值：** `int` - 受影响的总行数

**示例：**
```python
# 批量插入
users_data = [
    ('Alice', 25, 'alice@example.com'),
    ('Bob', 30, 'bob@example.com'),
    ('Charlie', 35, 'charlie@example.com'),
]

rows = await mysql.executemany(
    "INSERT INTO users (name, age, email) VALUES (%s, %s, %s)",
    args=users_data
)
print(f"批量插入了 {rows} 行")

# 批量更新
updates = [
    (26, 'Alice'),
    (31, 'Bob'),
    (36, 'Charlie'),
]

rows = await mysql.executemany(
    "UPDATE users SET age = %s WHERE name = %s",
    args=updates
)
print(f"批量更新了 {rows} 行")
```

## 完整使用示例

### 示例1：在 Spider 中使用

```python
from typing import Any, AsyncGenerator

from maize import Request, Response, Spider, SpiderSettings
from maize.utils.mysql_util import MysqlUtil


class DatabaseSpider(Spider):
    def __init__(self):
        super().__init__()
        self.mysql = None

    async def open(self, settings: SpiderSettings):
        """爬虫启动时初始化 MySQL 连接"""
        await super().open(settings)

        # 创建 MySQL 工具实例
        self.mysql = MysqlUtil(
            host=settings.mysql.host,
            port=settings.mysql.port,
            user=settings.mysql.user,
            password=settings.mysql.password,
            db=settings.mysql.db,
            minsize=5,
            maxsize=20
        )
        await self.mysql.open()
        self.logger.info("MySQL 连接池已创建")

    async def close(self):
        """爬虫关闭时清理资源"""
        if self.mysql:
            await self.mysql.close()
            self.logger.info("MySQL 连接池已关闭")

        await super().close()

    async def start_requests(self) -> AsyncGenerator[Request, Any]:
        # 从数据库获取待爬取的 URL
        urls = await self.mysql.fetchall(
            "SELECT url FROM task_queue WHERE status = %s LIMIT 10",
            args=('pending',)
        )

        for row in urls:
            yield Request(
                url=row['url'],
                meta={'task_id': row['id']}
            )

    async def parse(self, response: Response):
        task_id = response.meta.get('task_id')

        # 提取数据
        title = response.xpath('//title/text()').get()

        # 保存到数据库
        await self.mysql.execute(
            "INSERT INTO results (task_id, title, url) VALUES (%s, %s, %s)",
            args=(task_id, title, response.url)
        )

        # 更新任务状态
        await self.mysql.execute(
            "UPDATE task_queue SET status = %s WHERE id = %s",
            args=('completed', task_id)
        )


if __name__ == "__main__":
    settings = SpiderSettings(
        project_name="数据库爬虫",
        concurrency=5
    )

    # 配置 MySQL
    settings.mysql.host = "localhost"
    settings.mysql.port = 3306
    settings.mysql.db = "spider_db"
    settings.mysql.user = "root"
    settings.mysql.password = "password"

    DatabaseSpider().run(settings=settings)
```

### 示例2：在 Pipeline 中使用

```python
from typing import List

from maize import BasePipeline, Item, SpiderSettings
from maize.utils.mysql_util import MysqlSingletonUtil


class MysqlPipeline(BasePipeline):
    def __init__(self, settings: SpiderSettings):
        super().__init__(settings)
        self.mysql = None

    async def open(self):
        """Pipeline 初始化"""
        # 使用单例模式
        self.mysql = await MysqlSingletonUtil.get_instance(
            host=self.settings.mysql.host,
            port=self.settings.mysql.port,
            user=self.settings.mysql.user,
            password=self.settings.mysql.password,
            db=self.settings.mysql.db,
            minsize=10,
            maxsize=50
        )
        self.logger.info("MySQL Pipeline 已初始化")

    async def close(self):
        """Pipeline 关闭"""
        if self.mysql:
            await self.mysql.close()
            self.logger.info("MySQL Pipeline 已关闭")

    async def process_item(self, items: List[Item]) -> bool:
        """批量保存数据"""
        if not items:
            return True

        try:
            # 获取表名
            table_name = items[0].__table_name__
            if not table_name:
                self.logger.warning("Item 未设置 __table_name__，跳过保存")
                return True

            # 构建批量插入 SQL
            first_item = items[0].to_dict()
            columns = ', '.join(first_item.keys())
            placeholders = ', '.join(['%s'] * len(first_item))
            sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"

            # 准备数据
            values = [tuple(item.to_dict().values()) for item in items]

            # 批量插入
            rows = await self.mysql.executemany(sql, args=values)

            self.logger.info(f"成功插入 {rows} 条数据到 {table_name}")
            return True

        except Exception as e:
            self.logger.error(f"数据库插入失败: {e}")
            return False  # 返回 False 触发重试

    async def process_error_item(self, items: List[Item]):
        """处理失败的数据"""
        for item in items:
            self.logger.error(f"数据最终保存失败: {item.to_dict()}")
```

### 示例3：事务处理

```python
async def transfer_money(mysql: MysqlUtil, from_user_id: int, to_user_id: int, amount: float):
    """转账示例（需要事务支持）"""
    # 注意：MysqlUtil 默认自动提交，如需事务需要手动管理

    # 获取连接
    async with mysql.pool.acquire() as conn:
        async with conn.cursor() as cursor:
            try:
                # 开始事务
                await conn.begin()

                # 扣除发送方余额
                await cursor.execute(
                    "UPDATE accounts SET balance = balance - %s WHERE user_id = %s",
                    (amount, from_user_id)
                )

                # 增加接收方余额
                await cursor.execute(
                    "UPDATE accounts SET balance = balance + %s WHERE user_id = %s",
                    (amount, to_user_id)
                )

                # 记录转账记录
                await cursor.execute(
                    "INSERT INTO transactions (from_user, to_user, amount) VALUES (%s, %s, %s)",
                    (from_user_id, to_user_id, amount)
                )

                # 提交事务
                await conn.commit()
                print("转账成功")

            except Exception as e:
                # 回滚事务
                await conn.rollback()
                print(f"转账失败，已回滚: {e}")
                raise
```

## 最佳实践

### 1. 使用连接池

```python
# 根据并发数设置连接池大小
mysql = MysqlUtil(
    host="localhost",
    user="root",
    password="password",
    db="mydb",
    minsize=10,      # 最小连接数
    maxsize=50       # 最大连接数（建议设置为并发数的2-3倍）
)
```

### 2. 参数化查询（防止 SQL 注入）

```python
# ❌ 错误：字符串拼接（有 SQL 注入风险）
user_input = "1 OR 1=1"
sql = f"SELECT * FROM users WHERE id = {user_input}"

# ✅ 正确：参数化查询
user_input = "1 OR 1=1"
result = await mysql.fetchone(
    "SELECT * FROM users WHERE id = %s",
    args=(user_input,)
)
```

### 3. 批量操作优化

```python
# ❌ 低效：逐条插入
for item in items:
    await mysql.execute(
        "INSERT INTO products (name, price) VALUES (%s, %s)",
        args=(item['name'], item['price'])
    )

# ✅ 高效：批量插入
data = [(item['name'], item['price']) for item in items]
await mysql.executemany(
    "INSERT INTO products (name, price) VALUES (%s, %s)",
    args=data
)
```

### 4. 错误处理

```python
try:
    result = await mysql.fetchone("SELECT * FROM users WHERE id = %s", args=(1,))
    if result:
        print(result['name'])
    else:
        print("用户不存在")
except Exception as e:
    logger.error(f"数据库查询失败: {e}")
    # 进行错误处理
```

### 5. 资源管理

```python
# 使用 try-finally 确保连接池关闭
mysql = MysqlUtil(host="localhost", user="root", password="pass", db="mydb")
try:
    await mysql.open()
    # 执行数据库操作
    result = await mysql.fetchall("SELECT * FROM users")
finally:
    await mysql.close()
```

## 常见问题

### 1. 连接池大小如何设置？

建议：
- `minsize`: 设置为并发数的 1/2
- `maxsize`: 设置为并发数的 2-3 倍

例如并发数为 20：
```python
mysql = MysqlUtil(
    # ...其他参数
    minsize=10,
    maxsize=50
)
```

### 2. 如何处理连接超时？

```python
mysql = MysqlUtil(
    host="localhost",
    user="root",
    password="password",
    db="mydb",
    pool_recycle=3600  # 1小时后回收连接
)
```

### 3. 如何在多个 Spider 中共享连接池？

使用单例模式：
```python
# 在每个 Spider 中都获取同一个实例
mysql = await MysqlSingletonUtil.get_instance(
    host="localhost",
    user="root",
    password="password",
    db="mydb"
)
```

### 4. 返回的字典键名是什么？

返回的字典键名是数据库表的列名：
```python
result = await mysql.fetchone("SELECT id, name, age FROM users WHERE id = 1")
# result = {'id': 1, 'name': 'Alice', 'age': 25}
```

## 注意事项

1. **必须调用 open()**：使用前必须先调用 `open()` 初始化连接池
2. **记得调用 close()**：程序结束时调用 `close()` 释放资源
3. **使用参数化查询**：永远不要直接拼接 SQL 字符串
4. **批量操作**：大量数据操作时使用 `executemany()`
5. **异常处理**：数据库操作可能失败，需要妥善处理异常

## 下一步

- [Pipeline 管道](pipeline.md) - 了解如何在 Pipeline 中使用 MySQL
- [配置说明](settings.md) - MySQL 配置选项
- [RedisUtil](redis_util.md) - Redis 工具类使用
