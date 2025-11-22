# 数据管道 - Pipeline

## 简介

Pipeline（数据管道）是数据处理的核心组件，用于处理爬虫采集到的数据。数据会流经配置的所有管道进行处理。

### 主要功能

- **数据清洗**：去除无效数据、格式化数据
- **数据验证**：检查数据完整性和有效性
- **数据存储**：将数据保存到数据库、文件等
- **数据转换**：将数据转换为需要的格式

### 特性

- **批量处理**：框架会自动将多个 Item 聚合后批量处理，提高效率
- **异步支持**：支持异步操作，提高 I/O 性能
- **错误重试**：支持失败重试机制
- **多管道**：支持配置多个管道，按顺序执行

## 使用方式

### 1. 自定义 Pipeline

继承 `BasePipeline` 类并实现相关方法：

```python
from typing import List

from maize import BasePipeline, Item


class CustomPipeline(BasePipeline):
    async def open(self):
        """
        管道初始化时调用
        可以在这里初始化数据库连接、文件句柄等资源
        """
        self.logger.info("Pipeline 启动")
        # 初始化资源，如数据库连接
        # self.db_connection = await create_db_connection()

    async def close(self):
        """
        管道关闭时调用
        可以在这里清理资源、关闭连接等
        """
        self.logger.info("Pipeline 关闭")
        # 清理资源
        # await self.db_connection.close()

    async def process_item(self, items: List[Item]) -> bool:
        """
        处理数据（必须实现）

        :param items: Item 列表，框架会自动批量传入
        :return: True 表示处理成功，False 表示失败（会触发重试）
        """
        for item in items:
            print(f"处理数据: {item.to_dict()}")
            # 处理逻辑，如保存到数据库

        return True  # 返回 True 表示处理成功

    async def process_error_item(self, items: List[Item]):
        """
        处理超过重试次数的失败数据

        :param items: 失败的 Item 列表
        """
        for item in items:
            self.logger.error(f"处理失败的数据: {item.to_dict()}")
            # 可以保存到失败队列、写入日志文件等
```

### 2. 注册 Pipeline

#### 方式一：在 settings.py 中注册

```python
from maize import SpiderSettings


class Settings(SpiderSettings):
    # ...其他配置...
    pass


# 在创建 settings 对象后配置
settings = Settings()
settings.pipeline.pipelines = [
    "my_project.pipelines.CustomPipeline",
    "my_project.pipelines.MysqlPipeline",
]
```

#### 方式二：使用 SpiderSettings 对象

```python
from maize import SpiderSettings


settings = SpiderSettings(
    project_name="我的爬虫"
)
settings.pipeline.pipelines = [
    "my_project.pipelines.CustomPipeline"
]
```

#### 方式三：在 custom_settings 中注册

```python
class MySpider(Spider):
    custom_settings = {
        "pipeline": {
            "pipelines": ["my_project.pipelines.CustomPipeline"],
            "handle_batch_max_size": 50,
        }
    }
```

## 完整示例

### 示例1：控制台输出 Pipeline

```python
from typing import List

from maize import BasePipeline, Item


class ConsolePipeline(BasePipeline):
    """将数据输出到控制台"""

    async def process_item(self, items: List[Item]) -> bool:
        for item in items:
            print(f"[数据] {item.to_dict()}")
        return True
```

### 示例2：CSV 文件 Pipeline

```python
import csv
from pathlib import Path
from typing import List

from maize import BasePipeline, Item


class CsvPipeline(BasePipeline):
    """将数据保存到 CSV 文件"""

    async def open(self):
        """初始化文件"""
        self.file_path = Path("data.csv")
        self.file = open(self.file_path, "w", newline="", encoding="utf-8")
        self.writer = None
        self.headers_written = False

    async def close(self):
        """关闭文件"""
        if self.file:
            self.file.close()

    async def process_item(self, items: List[Item]) -> bool:
        if not items:
            return True

        # 写入表头（仅第一次）
        if not self.headers_written:
            headers = items[0].to_dict().keys()
            self.writer = csv.DictWriter(self.file, fieldnames=headers)
            self.writer.writeheader()
            self.headers_written = True

        # 写入数据
        for item in items:
            self.writer.writerow(item.to_dict())

        self.file.flush()  # 立即写入磁盘
        return True
```

### 示例3：MySQL Pipeline

```python
from typing import List

import aiomysql

from maize import BasePipeline, Item


class MysqlPipeline(BasePipeline):
    """将数据保存到 MySQL 数据库"""

    async def open(self):
        """创建数据库连接池"""
        settings = self.settings
        self.pool = await aiomysql.create_pool(
            host=settings.mysql.host,
            port=settings.mysql.port,
            user=settings.mysql.user,
            password=settings.mysql.password,
            db=settings.mysql.db,
            charset='utf8mb4'
        )
        self.logger.info("MySQL 连接池已创建")

    async def close(self):
        """关闭数据库连接池"""
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()
            self.logger.info("MySQL 连接池已关闭")

    async def process_item(self, items: List[Item]) -> bool:
        """批量插入数据"""
        if not items:
            return True

        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
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
                    await cursor.executemany(sql, values)
                    await conn.commit()

                    self.logger.info(f"成功插入 {len(items)} 条数据到 {table_name}")
                    return True

        except Exception as e:
            self.logger.error(f"数据库插入失败: {e}")
            return False  # 返回 False 触发重试

    async def process_error_item(self, items: List[Item]):
        """处理失败的数据"""
        for item in items:
            self.logger.error(f"数据最终保存失败: {item.to_dict()}")
            # 可以保存到错误日志文件
```

### 示例4：Redis Pipeline

```python
from typing import List

import redis.asyncio as redis
import ujson

from maize import BasePipeline, Item


class RedisPipeline(BasePipeline):
    """将数据保存到 Redis"""

    async def open(self):
        """创建 Redis 连接"""
        self.redis_client = await redis.from_url(
            self.settings.redis.url,
            encoding="utf-8",
            decode_responses=True
        )
        self.logger.info("Redis 连接已建立")

    async def close(self):
        """关闭 Redis 连接"""
        if self.redis_client:
            await self.redis_client.close()
            self.logger.info("Redis 连接已关闭")

    async def process_item(self, items: List[Item]) -> bool:
        """批量保存到 Redis"""
        try:
            # 使用 pipeline 批量操作
            pipe = self.redis_client.pipeline()

            for item in items:
                # 将数据保存到 Redis List
                data = ujson.dumps(item.to_dict())
                pipe.rpush("spider:items", data)

            await pipe.execute()
            self.logger.info(f"成功保存 {len(items)} 条数据到 Redis")
            return True

        except Exception as e:
            self.logger.error(f"Redis 保存失败: {e}")
            return False
```

### 示例5：数据清洗 Pipeline

```python
from typing import List

from maize import BasePipeline, Item


class DataCleaningPipeline(BasePipeline):
    """数据清洗管道"""

    async def process_item(self, items: List[Item]) -> bool:
        """清洗数据"""
        for item in items:
            # 去除标题前后空格
            if 'title' in item:
                item['title'] = item['title'].strip()

            # 价格转换为浮点数
            if 'price' in item:
                try:
                    # 去除价格中的非数字字符
                    price_str = ''.join(c for c in item['price'] if c.isdigit() or c == '.')
                    item['price'] = float(price_str)
                except (ValueError, AttributeError):
                    item['price'] = 0.0

            # URL 标准化
            if 'url' in item:
                if not item['url'].startswith('http'):
                    item['url'] = 'http://' + item['url']

        return True
```

## 配置 Pipeline 行为

### 批量处理配置

```python
from maize import SpiderSettings


settings = SpiderSettings()

# 正常数据处理配置
settings.pipeline.max_cache_count = 5000  # 内存队列最大缓存数量
settings.pipeline.handle_batch_max_size = 1000  # 每批处理的最大数量
settings.pipeline.handle_interval = 2  # 处理间隔（秒）

# 异常数据处理配置
settings.pipeline.error_max_retry_count = 5  # 最大重试次数
settings.pipeline.error_max_cache_count = 5000  # 异常数据队列最大缓存数量
settings.pipeline.error_retry_batch_max_size = 1  # 重试时每批处理数量（建议为1）
settings.pipeline.error_handle_batch_max_size = 1000  # 超过重试次数后每批处理数量
settings.pipeline.error_handle_interval = 60  # 处理异常数据的间隔（秒）
```

## 数据流程

```
爬虫 yield Item
    ↓
进入内存队列（缓存）
    ↓
达到批量条件（数量或时间）
    ↓
批量传递给 Pipeline
    ↓
process_item() 处理
    ↓
├─ 成功 → 完成
└─ 失败 → 进入错误队列
    ↓
    重试（最多 error_max_retry_count 次）
    ↓
    ├─ 成功 → 完成
    └─ 仍失败 → process_error_item() 处理
```

## 使用 Item

### 定义 Item

```python
from maize import Field, Item


class ProductItem(Item):
    __table_name__ = "products"  # 数据库表名（可选）

    name = Field()
    price = Field()
    url = Field()
    description = Field()
```

### 在爬虫中使用

```python
from maize import Spider, Response
from my_project.items import ProductItem


class MySpider(Spider):
    async def parse(self, response: Response):
        item = ProductItem()
        item["name"] = response.xpath('//h1/text()').get()
        item["price"] = response.xpath('//span[@class="price"]/text()').get()
        item["url"] = response.url
        item["description"] = response.xpath('//div[@class="desc"]/text()').get()

        yield item  # 提交到 Pipeline 处理
```

### Item 方法

```python
item = ProductItem()
item["name"] = "商品名称"

# 转换为字典
data = item.to_dict()
# {'name': '商品名称', 'price': None, 'url': None, 'description': None}

# 获取表名
table_name = item.__table_name__  # "products"

# 获取重试次数
retry_count = item.__retry_count__
```

## 多管道处理

可以配置多个管道，按顺序执行：

```python
settings = SpiderSettings()
settings.pipeline.pipelines = [
    "my_project.pipelines.DataCleaningPipeline",  # 1. 数据清洗
    "my_project.pipelines.DataValidationPipeline",  # 2. 数据验证
    "my_project.pipelines.MysqlPipeline",  # 3. 保存到 MySQL
    "my_project.pipelines.RedisPipeline",  # 4. 保存到 Redis
]
```

**注意**：如果某个管道的 `process_item` 返回 `False`，数据不会传递到后续管道，而是进入重试队列。

## 最佳实践

### 1. 资源管理

始终在 `open()` 中初始化资源，在 `close()` 中释放：

```python
class MyPipeline(BasePipeline):
    async def open(self):
        self.resource = await create_resource()

    async def close(self):
        await self.resource.close()
```

### 2. 异常处理

在 `process_item` 中捕获异常，返回 False 触发重试：

```python
async def process_item(self, items: List[Item]) -> bool:
    try:
        # 处理逻辑
        await save_to_db(items)
        return True
    except Exception as e:
        self.logger.error(f"处理失败: {e}")
        return False  # 触发重试
```

### 3. 批量操作

充分利用批量处理提高效率：

```python
async def process_item(self, items: List[Item]) -> bool:
    # 不推荐：逐条插入
    # for item in items:
    #     await db.insert_one(item)

    # 推荐：批量插入
    await db.insert_many(items)
    return True
```

### 4. 数据验证

在 Pipeline 中验证数据完整性：

```python
async def process_item(self, items: List[Item]) -> bool:
    valid_items = []

    for item in items:
        # 验证必填字段
        if not item.get('title') or not item.get('url'):
            self.logger.warning(f"数据不完整，跳过: {item.to_dict()}")
            continue

        valid_items.append(item)

    if valid_items:
        await self.save_to_db(valid_items)

    return True
```

### 5. 使用连接池

对于数据库操作，使用连接池提高性能：

```python
class MysqlPipeline(BasePipeline):
    async def open(self):
        # 创建连接池而不是单个连接
        self.pool = await aiomysql.create_pool(
            host=self.settings.mysql.host,
            # ...其他配置
            minsize=5,  # 最小连接数
            maxsize=20  # 最大连接数
        )
```

## 注意事项

1. **process_item 必须返回 bool**：返回 True 表示成功，False 表示失败需要重试
2. **避免阻塞操作**：使用异步操作避免阻塞事件循环
3. **批量处理**：items 参数是列表，充分利用批量操作
4. **错误处理**：合理使用 process_error_item 处理最终失败的数据
5. **资源释放**：确保在 close() 中释放所有资源

## 下一步

- [Item 详解](item.md) - 了解 Item 的详细用法
- [配置说明](settings.md) - Pipeline 相关配置
- [Spider 进阶](spider.md) - 在爬虫中使用 Pipeline
