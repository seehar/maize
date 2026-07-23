# 同步爬虫

maize 从 v0.6.0 起提供同步爬虫模块 `maize.sync`，与异步爬虫 `maize.aio` 一一对应。
同步爬虫使用 `httpx.Client`（同步模式）发起请求，`threading` 线程池实现并发，
适合不希望使用 asyncio 的场景，或在同步代码库中快速集成爬虫功能。

## 与异步爬虫的对应关系

| 异步 (`maize.aio`) | 同步 (`maize.sync`) | 说明 |
|---|---|---|
| `LiteSpider` | `SyncLiteSpider` | 轻量爬虫，构造函数配置 |
| `LiteCrawler` | `SyncLiteCrawler` | Lite 运行器，线程池并发 |
| `Spider` | `SyncSpider` | Classic 爬虫基类 |
| `TaskSpider` | `SyncTaskSpider` | 任务爬虫 |
| `CrawlerProcess` | `SyncCrawlerProcess` | 多 Spider 运行入口 |
| `AioEngine` | `SyncEngine` | 引擎，线程池替代 asyncio |
| `BaseDownloader` | `SyncBaseDownloader` | 下载器基类 |
| `HTTPXDownloader` | `SyncHttpxDownloader` | httpx 下载器 |
| - | `SyncRequestsDownloader` | requests 下载器（额外依赖） |
| `BaseMiddleware` | `SyncBaseMiddleware` | 中间件基类 |
| `BasePipeline` | `SyncBasePipeline` | 管道基类 |
| `Scheduler` | `SyncScheduler` | 调度器 |
| `Processor` | `SyncProcessor` | 处理器 |
| `StatsCollector` | `SyncStatsCollector` | 统计收集器 |
| `SpiderPriorityQueue` | `SyncSpiderPriorityQueue` | 优先级队列 |

## 两档模式

### SyncLite（轻量级同步爬虫）

- `SyncLiteSpider`: `httpx.Client` 同步模式，构造函数配置
- `SyncLiteCrawler`: `threading` + `queue.PriorityQueue` 线程池并发
- 支持去重、深度控制、`per_domain_concurrency`、重试、优雅关闭
- aiohttp 单依赖，不引入中间件/管道/调度器抽象

```python
from maize.common.http import Request, Response
from maize.sync.lite import SyncLiteSpider


class MySpider(SyncLiteSpider):
    def start_requests(self):
        yield Request(url="https://example.com")

    def parse(self, response: Response):
        self.logger.info(response.text[:100])


if __name__ == "__main__":
    MySpider().run()
```

### SyncClassic（完整同步爬虫）

- `SyncSpider` / `SyncTaskSpider`: 同步生成器 API
- `SyncEngine`: 线程池引擎，中间件链/调度器/处理器完整
- `SyncBaseDownloader` + `SyncHttpxDownloader` + `SyncRequestsDownloader`
- 同步版中间件管理器（Downloader/Spider/Pipeline 三层）
- 同步版管道调度器（批量/错误重试）
- `SyncCrawlerProcess`: 多 Spider 运行入口

```python
from collections.abc import Generator
from maize import Request, Response, SpiderSettings, SyncSpider, SyncSpiderDownloaderEnum
from maize.sync.classic.crawler.sync_crawler import SyncCrawlerProcess


class MySpider(SyncSpider):
    def start_requests(self) -> Generator[Request, None, None]:
        yield Request(url="https://example.com")

    def parse(self, response: Response):
        self.logger.info(response.text[:100])


settings = SpiderSettings(
    project_name="my_project",
    concurrency=3,
    downloader=SyncSpiderDownloaderEnum.HTTPX.value,
)

process = SyncCrawlerProcess(settings=settings)
process.crawl(MySpider)
process.start()
```

## 下载器选择

同步爬虫支持两种下载器：

| 下载器 | 枚举 | 依赖 | 特点 |
|---|---|---|---|
| `SyncHttpxDownloader` | `SyncSpiderDownloaderEnum.HTTPX` | httpx（已安装） | 零额外依赖，连接池复用 |
| `SyncRequestsDownloader` | `SyncSpiderDownloaderEnum.REQUESTS` | requests | 生态成熟，需 `pip install requests` |

```python
from maize import SpiderSettings, SyncSpiderDownloaderEnum

# httpx（默认）
settings = SpiderSettings(downloader=SyncSpiderDownloaderEnum.HTTPX.value)

# requests
settings = SpiderSettings(downloader=SyncSpiderDownloaderEnum.REQUESTS.value)
```

## 中间件

同步爬虫的中间件与异步版 API 一致，但所有方法为同步（非 async）：

```python
from maize.sync.classic.middleware.sync_base_middleware import SyncDownloaderMiddleware


class MyMiddleware(SyncDownloaderMiddleware):
    def open(self):
        pass

    def close(self):
        pass

    def process_request(self, request, spider):
        # 返回 request 继续传递，返回 Response 短路，返回 None 丢弃
        return request

    def process_response(self, request, response, spider):
        return response

    def process_exception(self, request, exception, spider):
        return None
```

注册中间件：

```python
settings.middleware.downloader_middlewares = {MyMiddleware: 100}
```

## 管道

同步管道用于数据落盘：

```python
from maize.sync.classic.pipeline.sync_base_pipeline import SyncBasePipeline


class MyPipeline(SyncBasePipeline):
    def open(self):
        pass

    def close(self):
        pass

    def process_item(self, items: list) -> bool:
        for item in items:
            print(item)
        return True

    def process_error_item(self, items: list):
        pass
```

注册管道：

```python
settings.pipeline.pipelines = [MyPipeline]
# 或使用字符串路径
settings.pipeline.pipelines = ["my_module.MyPipeline"]
```

## 关键差异

| 特性 | 异步爬虫 | 同步爬虫 |
|---|---|---|
| 并发模型 | asyncio 事件循环 | threading 线程池 |
| 请求库 | aiohttp / httpx.AsyncClient | httpx.Client / requests |
| 中间件方法 | `async def` | 同步 `def` |
| 管道方法 | `async def` | 同步 `def` |
| 分布式 | 支持 Redis | 不支持 |
| 信号处理 | `loop.add_signal_handler` | `signal.signal`（仅主线程） |
| 统计上传 | asyncio.Task 后台上传 | 同步上传 |

## API

::: maize.sync.lite.spider.sync_lite_spider.SyncLiteSpider
::: maize.sync.classic.spider.sync_spider.SyncSpider
::: maize.sync.classic.crawler.sync_crawler.SyncCrawlerProcess
