# 简介及安装

> maize 是一个基于异步、强大易用的 Python 爬虫框架

## 特性

- 🚀 **异步高性能**：基于 asyncio 实现，支持高并发采集
- 🎯 **简单易用**：提供简洁的 API，快速上手
- 🔧 **灵活配置**：支持多种配置方式（代码、配置文件、环境变量）
- 📦 **插件化设计**：下载器、管道、中间件均可自定义扩展
- 🌐 **多种下载器**：内置 aiohttp、httpx、playwright、patchright 下载器
- 🤖 **RPA 支持**：集成浏览器自动化，支持复杂页面采集
- 📊 **数据管道**：支持多管道并行处理，自动批量入库
- 🔄 **分布式支持**：基于 Redis 实现分布式爬虫
- ⏸️ **暂停/继续**：支持爬虫暂停和继续功能
- 📝 **日志系统**：灵活的日志配置，支持自定义日志处理器

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

根据需要安装额外功能：

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

### 方式一：简单爬虫

最简单的爬虫示例：

```python
from maize import Request, Response, Spider


class BaiduSpider(Spider):
    async def start_requests(self):
        yield Request(url="http://www.baidu.com")

    async def parse(self, response: Response):
        self.logger.info(f"响应状态码: {response.status}")
        self.logger.info(f"响应内容: {response.text[:100]}...")


if __name__ == "__main__":
    BaiduSpider().run()
```

### 方式二：使用配置对象

使用 SpiderSettings 对象进行配置：

```python
from maize import Request, Response, Spider, SpiderSettings


class SimpleSpider(Spider):
    async def start_requests(self):
        yield Request(url="http://www.baidu.com")

    async def parse(self, response: Response):
        print(response.text[:100])


if __name__ == "__main__":
    settings = SpiderSettings(
        project_name="简单爬虫",
        concurrency=5,
        log_level="DEBUG",
        downloader="maize.HTTPXDownloader"
    )

    SimpleSpider().run(settings=settings)
```

### 方式三：装饰器方式启动爬虫

使用装饰器注册并启动多个爬虫：

```python
from typing import Any, AsyncGenerator

from maize import Request, Response, Spider, SpiderEntry

spider_entry = SpiderEntry()


@spider_entry.register(settings={"downloader": "maize.HTTPXDownloader"})
class DecoratorSpider(Spider):
    async def start_requests(self) -> AsyncGenerator[Request, Any]:
        yield Request(url="http://www.baidu.com")

    async def parse(self, response: Response):
        print(response.text[:100])


@spider_entry.register(settings={"concurrency": 3})
class AnotherSpider(Spider):
    async def start_requests(self) -> AsyncGenerator[Request, Any]:
        yield Request(url="http://www.example.com")

    async def parse(self, response: Response):
        print(response.status)


if __name__ == "__main__":
    spider_entry.run()
```

### 方式四：使用配置文件

创建 `settings.py` 配置文件：

```python
# settings.py
from maize import SpiderSettings


class Settings(SpiderSettings):
    project_name = "我的爬虫项目"
    concurrency = 10
    log_level = "INFO"
    downloader = "maize.AioHttpDownloader"
```

在爬虫中使用配置文件：

```python
from maize import Request, Response, Spider


class MySpider(Spider):
    async def start_requests(self):
        yield Request(url="http://www.example.com")

    async def parse(self, response: Response):
        print(response.text)


if __name__ == "__main__":
    # 自动加载当前目录下的 settings.Settings 类
    MySpider().run(settings_path="settings.Settings")
```

## 核心概念

### Spider（爬虫）

`Spider` 是爬虫的核心类，需要继承并实现 `start_requests` 和 `parse` 方法：

- **start_requests**：生成初始请求
- **parse**：解析响应，可以 yield Request（新请求）或 Item（数据）

### Request（请求）

`Request` 封装了 HTTP 请求的所有参数，支持：

- 多种 HTTP 方法（GET、POST、PUT 等）
- 自定义请求头、参数、数据
- 代理支持
- 优先级控制
- 自定义回调函数

### Response（响应）

`Response` 封装了 HTTP 响应，提供便捷的数据提取方法：

- `text`：响应文本
- `body`：响应二进制数据
- `json()`：解析 JSON
- `xpath()`：XPath 选择器
- `css()`：CSS 选择器

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

### SpiderSettings（配置）

`SpiderSettings` 是配置类，支持多种配置方式：

- 代码配置
- 配置文件（支持 .env、.yaml、.toml）
- 环境变量

### Pipeline（数据管道）

`Pipeline` 用于处理采集到的数据，支持自定义数据处理逻辑：

- 数据清洗
- 数据验证
- 数据入库
- 数据转换

## 下一步

- [快速上手](quick_start.md)：了解更多使用示例
- [Spider 进阶](features/spider.md)：学习高级特性
- [配置说明](features/settings.md)：详细的配置选项
- [Request 详解](features/request.md)：请求参数说明
- [Response 详解](features/response.md)：响应处理方法
- [Pipeline 管道](features/pipeline.md)：数据管道使用
- [下载器](features/downloader.md)：下载器配置与自定义
