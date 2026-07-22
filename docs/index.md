# 简介及安装

> maize 是一个基于 asyncio 的轻量级异步 Python 爬虫框架，提供 Lite 和 Classic 两种使用模式。

## 特性

- 🚀 **异步高性能**：基于 asyncio 实现，高并发采集
- 🎯 **双模式**：Lite 轻量开箱即用，Classic 完整中间件/管道/调度器
- 🧩 **中间件系统**：下载器/爬虫/管道三层中间件，可插拔扩展
- 📦 **插件化下载器**：内置 aiohttp、httpx、playwright、patchright
- 🤖 **RPA 支持**：浏览器自动化，动态页面采集与反检测
- 📊 **数据管道**：多管道并行，批量入库，支持 MySQL/Redis/CSV 等
- 🔄 **分布式支持**：基于 Redis 实现分布式爬虫
- ⏸️ **暂停/继续**：爬虫运行时暂停和恢复
- 📝 **灵活配置**：代码、配置文件、环境变量、YAML/TOML 多方式配置

## 两种爬虫模式

maize 提供 Lite 和 Classic 两种模式，按场景选择：

| 维度 | Lite Spider | Classic Spider |
|------|-------------|----------------|
| 定位 | 轻量开箱即用，单文件即跑 | 完整功能，中间件/管道/调度器 |
| 依赖 | aiohttp 单依赖 | 可选 MySQL/Redis/Playwright |
| 配置 | 构造函数参数 + 可重写属性 | SpiderSettings 文件/对象/环境变量 |
| 中间件 | 不支持 | 三层中间件链 |
| 数据管道 | `process_item` 钩子 | Pipeline 链（批量入库） |
| 去重/深度 | 内置（可关闭） | 中间件实现 |
| 适用场景 | 简单抓取、API 采集、监控轮询 | 大型项目、多管道、分布式 |

- **Lite 模式**：5 分钟上手，适合简单抓取。详见 [Lite 轻量爬虫](features/lite_spider.md)。
- **Classic 模式**：完整功能，适合大型项目。详见 [Spider 进阶](features/spider.md)。

## 环境要求

- Python 3.10+
- Linux, Windows, macOS

## 安装

### 基础安装

=== "pip"
    ```shell
    pip install maize
    ```

=== "poetry"
    ```shell
    poetry add maize
    ```

=== "uv"
    ```shell
    uv add maize
    ```

### 可选依赖

=== "RPA 支持（Playwright/Patchright）"
    ```shell
    pip install maize[rpa]
    # 安装浏览器驱动
    playwright install
    ```

=== "MySQL 支持"
    ```shell
    pip install maize[mysql]
    ```

=== "Redis 分布式支持"
    ```shell
    pip install maize[redis]
    ```

=== "完整安装"
    ```shell
    pip install maize[all]
    ```

## 快速开始

### 方式一：Lite 爬虫（推荐入门）

最轻量的用法，无需配置文件，构造函数即用：

```python
from maize.aio.lite import LiteSpider, Request, Response

class MySpider(LiteSpider):
    async def start_requests(self):
        yield Request(url="https://example.com")

    async def parse(self, response: Response):
        self.logger.info(f"状态码: {response.status}")
        self.logger.info(f"标题: {response.xpath('//title/text()').get()}")

if __name__ == "__main__":
    MySpider().run()
```

Lite 爬虫内置并发、重试、代理、请求去重、深度控制、优先级队列、优雅关闭，
详见 [Lite 轻量爬虫](features/lite_spider.md)。

### 方式二：Classic Spider + 配置对象

```python
from maize import Request, Response, Spider, SpiderSettings, SpiderDownloaderEnum, LogLevelEnum

class SimpleSpider(Spider):
    async def start_requests(self):
        yield Request(url="http://www.baidu.com")

    async def parse(self, response: Response):
        self.logger.info(response.text[:100])

if __name__ == "__main__":
    settings = SpiderSettings(
        project_name="简单爬虫",
        concurrency=5,
        log_level=LogLevelEnum.DEBUG.value,
        downloader=SpiderDownloaderEnum.HTTPX.value
    )
    SimpleSpider().run(settings=settings)
```

### 方式三：装饰器方式启动多个爬虫

```python
from typing import Any, AsyncGenerator

from maize import Request, Response, Spider, SpiderEntry, SpiderDownloaderEnum, LogLevelEnum

spider_entry = SpiderEntry()

@spider_entry.register(settings={"downloader": SpiderDownloaderEnum.HTTPX.value})
class DecoratorSpider(Spider):
    async def start_requests(self) -> AsyncGenerator[Request, Any]:
        yield Request(url="http://www.baidu.com")

    async def parse(self, response: Response):
        self.logger.info(response.text[:100])

@spider_entry.register(settings={"concurrency": 3})
class AnotherSpider(Spider):
    async def start_requests(self) -> AsyncGenerator[Request, Any]:
        yield Request(url="http://www.example.com")

    async def parse(self, response: Response):
        self.logger.info(response.status)

if __name__ == "__main__":
    spider_entry.run()
```

### 方式四：配置文件

创建 `settings.py` 配置文件：

```python
# settings.py
from maize import SpiderSettings, SpiderDownloaderEnum, LogLevelEnum

class Settings(SpiderSettings):
    project_name: str = "我的爬虫项目"
    concurrency: int = 10
    log_level: str = LogLevelEnum.INFO.value
    downloader: str = SpiderDownloaderEnum.AIOHTTP.value
```

在爬虫中使用配置文件：

```python
from maize import Request, Response, Spider

class MySpider(Spider):
    async def start_requests(self):
        yield Request(url="http://www.example.com")

    async def parse(self, response: Response):
        self.logger.info(response.text)

if __name__ == "__main__":
    # 自动加载当前目录下的 settings.Settings 类
    MySpider().run(settings_path="settings.Settings")
```

## 核心概念

### Spider（爬虫）

maize 提供两种爬虫模式：

- **Lite Spider**：轻量级，内置并发、重试、代理、去重、深度控制，无中间件
- **Classic Spider**：完整功能，支持中间件、管道、调度器

### Request / Response

- **start_requests**：生成初始请求
- **parse**：解析响应，可以 yield Request（新请求）或 Item（数据）

`Request` 封装 HTTP 请求参数，支持多种方法、自定义头、代理、优先级、自定义回调。
`Response` 封装响应，提供 `text`、`body`、`json()`、`xpath()`、`css()` 等方法。

### Item（数据项）

`Item` 用于定义采集的数据结构：

```python
from maize import Field, Item

class MyItem(Item):
    __table_name__ = "my_table"  # 数据库表名（可选）

    title = Field()
    url = Field()
    content = Field()
```

### Pipeline（数据管道）

- **Classic 模式**：Pipeline 链，多管道并行处理，自动批量入库
- **Lite 模式**：`process_item` 钩子，轻量数据落盘

### 中间件系统

Classic 模式提供三层中间件：下载器中间件、爬虫中间件、管道中间件，
支持请求/响应处理、URL 过滤、数据清洗等扩展。
详见 [中间件系统](features/middleware.md)。

### SpiderSettings（配置）

`SpiderSettings` 支持：代码配置、配置文件（.env/.yaml/.toml）、环境变量。

## 下一步

- [Lite 轻量爬虫](features/lite_spider.md) - 快速上手轻量级爬虫
- [Spider 进阶](features/spider.md) - Classic Spider 高级特性
- [配置说明](features/settings.md) - 详细的配置选项
- [中间件系统](features/middleware.md) - 中间件配置与自定义
- [Request 详解](features/request.md)：请求参数说明
- [Response 详解](features/response.md)：响应处理方法
- [Pipeline 管道](features/pipeline.md)：数据管道使用
- [下载器](features/downloader.md)：下载器配置与自定义
