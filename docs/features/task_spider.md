# TaskSpider 任务爬虫

> 在实际应用中，经常需要持续性地获取采集任务。每批任务采集完成后，再从数据源获取或生成新的一批采集任务。
> 此时，使用任务爬虫 `TaskSpider` 代替普通的 `Spider`，是一个更优的选择。
>
> 任务爬虫在 [Spider](./spider.md) 的基础上，增加了分批获取任务的能力。

## 简介

`TaskSpider` 的核心特性：

- **自动调度**：框架会自动调用 `start_requests` 方法获取任务
- **批量处理**：支持分批次获取和处理任务
- **任务续航**：当前批次任务完成后，自动获取下一批任务
- **优雅退出**：当无更多任务时，通过抛出 `StopAsyncIteration` 异常优雅地结束爬虫

## 使用场景

TaskSpider 适用于以下场景：

1. **数据库任务队列**：从数据库中分批读取待爬取的 URL
2. **API 任务源**：从 API 接口持续获取采集任务
3. **文件任务队列**：从文件中分批读取待处理的任务
4. **消息队列**：从 Redis、RabbitMQ 等消息队列中获取任务
5. **增量采集**：持续监控数据源，采集新增内容

## 基本使用

### 最简单的示例

```python
import typing
from typing import Any, AsyncGenerator

from maize import Request, Response, TaskSpider


class DemoTaskSpider(TaskSpider):
    batch_count = 0  # 批次计数器

    async def start_requests(self) -> AsyncGenerator[Request, Any]:
        """
        生成采集任务
        当无更多任务时，抛出 StopAsyncIteration 异常
        """
        self.batch_count += 1

        # 假设只采集3批任务
        if self.batch_count > 3:
            # 无更多任务，抛出异常结束
            raise StopAsyncIteration

        self.logger.info(f"正在生成第 {self.batch_count} 批任务")

        # 生成本批次的采集任务
        for i in range(5):
            yield Request(url=f"http://www.example.com/page{i}")

    async def parse(self, response: Response):
        """解析响应"""
        self.logger.info(f"解析页面: {response.url}")
        # 处理数据...


if __name__ == "__main__":
    DemoTaskSpider().run()
```

### 从数据库获取任务

```python
import typing
from typing import Any, AsyncGenerator

import aiomysql

from maize import Request, Response, TaskSpider, SpiderSettings


class DatabaseTaskSpider(TaskSpider):
    def __init__(self):
        super().__init__()
        self.db_pool = None
        self.batch_size = 100  # 每批次获取的任务数
        self.last_id = 0  # 记录上次获取的最后一条记录ID

    async def open(self, settings: SpiderSettings):
        """初始化时创建数据库连接池"""
        await super().open(settings)

        self.db_pool = await aiomysql.create_pool(
            host=settings.mysql.host,
            port=settings.mysql.port,
            user=settings.mysql.user,
            password=settings.mysql.password,
            db=settings.mysql.db,
        )
        self.logger.info("数据库连接池已创建")

    async def close(self):
        """关闭时清理数据库连接池"""
        if self.db_pool:
            self.db_pool.close()
            await self.db_pool.wait_closed()
            self.logger.info("数据库连接池已关闭")

        await super().close()

    async def start_requests(self) -> AsyncGenerator[Request, Any]:
        """从数据库获取待采集的任务"""
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # 查询待采集的URL
                sql = """
                    SELECT id, url FROM task_queue
                    WHERE id > %s AND status = 'pending'
                    ORDER BY id ASC
                    LIMIT %s
                """
                await cursor.execute(sql, (self.last_id, self.batch_size))
                tasks = await cursor.fetchall()

                if not tasks:
                    # 没有更多任务，结束爬虫
                    self.logger.info("没有更多待采集任务")
                    raise StopAsyncIteration

                self.logger.info(f"获取到 {len(tasks)} 个待采集任务")

                for task_id, url in tasks:
                    self.last_id = task_id
                    yield Request(
                        url=url,
                        meta={'task_id': task_id}  # 传递任务ID
                    )

    async def parse(self, response: Response):
        """解析响应并更新任务状态"""
        task_id = response.request.meta.get('task_id')

        # 提取数据...
        title = response.xpath('//title/text()').get()

        # 更新任务状态
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    "UPDATE task_queue SET status = 'completed' WHERE id = %s",
                    (task_id,)
                )
                await conn.commit()

        yield {'task_id': task_id, 'title': title, 'url': response.url}


if __name__ == "__main__":
    settings = SpiderSettings(
        project_name="数据库任务爬虫",
        concurrency=10,
    )
    DatabaseTaskSpider().run(settings=settings)
```

### 从 API 获取任务

```python
import httpx
from typing import Any, AsyncGenerator

from maize import Request, Response, TaskSpider, SpiderSettings


class ApiTaskSpider(TaskSpider):
    def __init__(self):
        super().__init__()
        self.api_url = "http://api.example.com/tasks"
        self.page = 0

    async def start_requests(self) -> AsyncGenerator[Request, Any]:
        """从 API 获取采集任务"""
        self.page += 1

        # 调用 API 获取任务列表
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.api_url,
                params={'page': self.page, 'size': 50}
            )
            data = response.json()

        tasks = data.get('tasks', [])

        if not tasks:
            self.logger.info("API 返回空任务列表，结束采集")
            raise StopAsyncIteration

        self.logger.info(f"从 API 获取到 {len(tasks)} 个任务")

        for task in tasks:
            yield Request(
                url=task['url'],
                meta={'task_info': task}
            )

    async def parse(self, response: Response):
        task_info = response.request.meta.get('task_info')
        self.logger.info(f"处理任务: {task_info.get('id')}")

        # 提取和处理数据...
        yield {
            'task_id': task_info.get('id'),
            'url': response.url,
            'title': response.xpath('//title/text()').get()
        }


if __name__ == "__main__":
    ApiTaskSpider().run()
```

### 从 Redis 队列获取任务

```python
import redis.asyncio as redis
from typing import Any, AsyncGenerator

from maize import Request, Response, TaskSpider, SpiderSettings


class RedisTaskSpider(TaskSpider):
    def __init__(self):
        super().__init__()
        self.redis_client = None
        self.queue_key = "spider:tasks"
        self.batch_size = 50

    async def open(self, settings: SpiderSettings):
        """初始化 Redis 连接"""
        await super().open(settings)

        self.redis_client = await redis.from_url(settings.redis.url)
        self.logger.info("Redis 连接已建立")

    async def close(self):
        """关闭 Redis 连接"""
        if self.redis_client:
            await self.redis_client.close()
            self.logger.info("Redis 连接已关闭")

        await super().close()

    async def start_requests(self) -> AsyncGenerator[Request, Any]:
        """从 Redis 队列获取任务"""
        # 从 Redis 列表中批量获取任务
        tasks = []
        for _ in range(self.batch_size):
            task = await self.redis_client.lpop(self.queue_key)
            if task:
                tasks.append(task.decode('utf-8'))
            else:
                break

        if not tasks:
            self.logger.info("Redis 队列为空，等待新任务...")
            # 可以选择等待一段时间后重试，或者直接结束
            raise StopAsyncIteration

        self.logger.info(f"从 Redis 获取到 {len(tasks)} 个任务")

        for task_url in tasks:
            yield Request(url=task_url)

    async def parse(self, response: Response):
        """解析响应"""
        self.logger.info(f"处理: {response.url}")
        # 处理数据...
        yield {
            'url': response.url,
            'title': response.xpath('//title/text()').get()
        }


if __name__ == "__main__":
    settings = SpiderSettings(
        project_name="Redis任务爬虫",
        concurrency=10,
    )
    RedisTaskSpider().run(settings=settings)
```

## TaskSpider vs Spider

| 特性       | Spider                | TaskSpider              |
|:---------|:----------------------|:------------------------|
| 任务来源     | 固定的初始URL列表           | 动态获取，支持分批               |
| 使用场景     | 已知的URL列表，或通过解析页面发现URL | 从外部数据源持续获取任务            |
| 任务续航     | 所有初始任务完成后结束           | 支持持续获取新任务，直到数据源无更多任务     |
| 适合的数据源   | 静态列表、网站导航结构           | 数据库、API、消息队列、文件等        |
| start_requests | 只调用一次                 | 每批任务完成后会再次调用 |

## 最佳实践

### 1. 合理设置批次大小

```python
class MyTaskSpider(TaskSpider):
    batch_size = 100  # 根据实际情况调整

    async def start_requests(self):
        # 每次获取 batch_size 个任务
        tasks = await self.fetch_tasks_from_source(self.batch_size)

        if not tasks:
            raise StopAsyncIteration

        for task in tasks:
            yield Request(url=task['url'])
```

### 2. 添加任务状态追踪

```python
class MyTaskSpider(TaskSpider):
    async def start_requests(self):
        tasks = await self.get_pending_tasks()

        if not tasks:
            raise StopAsyncIteration

        for task in tasks:
            # 标记任务为处理中
            await self.mark_task_as_processing(task['id'])

            yield Request(
                url=task['url'],
                meta={'task_id': task['id']}
            )

    async def parse(self, response: Response):
        task_id = response.request.meta['task_id']

        try:
            # 处理数据
            data = self.extract_data(response)

            # 标记任务为完成
            await self.mark_task_as_completed(task_id)

            yield data
        except Exception as e:
            # 标记任务为失败
            await self.mark_task_as_failed(task_id, str(e))
            raise
```

### 3. 优雅地处理空任务

```python
class MyTaskSpider(TaskSpider):
    max_empty_retries = 3  # 最大空任务重试次数
    empty_retry_count = 0

    async def start_requests(self):
        tasks = await self.fetch_tasks()

        if not tasks:
            self.empty_retry_count += 1

            if self.empty_retry_count >= self.max_empty_retries:
                self.logger.info(f"连续 {self.max_empty_retries} 次获取到空任务，结束爬虫")
                raise StopAsyncIteration

            self.logger.info(f"暂无任务，等待 10 秒后重试...")
            await asyncio.sleep(10)
            # 返回空生成器，等待下次调用
            return

        # 重置计数器
        self.empty_retry_count = 0

        for task in tasks:
            yield Request(url=task['url'])
```

### 4. 结合错误处理

```python
class MyTaskSpider(TaskSpider):
    async def start_requests(self):
        tasks = await self.fetch_tasks()

        if not tasks:
            raise StopAsyncIteration

        for task in tasks:
            yield Request(
                url=task['url'],
                callback=self.parse,
                error_callback=self.handle_error,
                meta={'task': task}
            )

    async def parse(self, response: Response):
        # 正常处理
        pass

    async def handle_error(self, request: Request):
        """处理请求失败"""
        task = request.meta['task']
        self.logger.error(f"任务失败: {task}")

        # 标记任务失败，或重新入队
        await self.mark_task_as_failed(task['id'])
```

## 注意事项

1. **必须抛出 StopAsyncIteration**：当无更多任务时，必须抛出 `StopAsyncIteration` 异常，否则框架会持续调用 `start_requests`

2. **避免无限循环**：确保在某个条件下会抛出 `StopAsyncIteration`，否则爬虫将永不停止

3. **资源管理**：如果使用了数据库连接、Redis 连接等资源，记得在 `open()` 中初始化，在 `close()` 中释放

4. **并发控制**：TaskSpider 同样支持并发，通过 `concurrency` 参数控制

5. **任务幂等性**：考虑任务的幂等性，避免重复处理相同的任务

## 下一步

- [Spider 进阶](spider.md) - 学习更多 Spider 特性
- [配置说明](settings.md) - 详细的配置选项
- [Pipeline 管道](pipeline.md) - 数据管道使用
