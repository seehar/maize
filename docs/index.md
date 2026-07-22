# 简介及安装

> maize 是一个基于 asyncio 的轻量级异步 Python 爬虫框架，提供 Lite 和 Classic 两种使用模式。

## 特性

- **异步高性能** — 基于 asyncio 实现，高并发采集
- **双模式** — Lite 轻量开箱即用，Classic 完整中间件/管道/调度器
- **中间件系统** — 下载器/爬虫/管道三层中间件，可插拔扩展
- **插件化下载器** — 内置 aiohttp、httpx、playwright、patchright
- **RPA 支持** — 浏览器自动化，动态页面采集与反检测
- **数据管道** — 多管道并行，批量入库，支持 MySQL/Redis/CSV 等
- **分布式支持** — 基于 Redis 实现分布式爬虫
- **暂停/继续** — 爬虫运行时暂停和恢复
- **灵活配置** — 代码、配置文件、环境变量、YAML/TOML 多方式配置

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

模式选择决策表和模块对照表详见 [使用前必读](use/before_use.md)。

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

### Lite 爬虫（推荐入门）

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

### Classic Spider

```python
from maize import Request, Response, Spider, SpiderSettings

class MySpider(Spider):
    async def start_requests(self):
        yield Request(url="http://www.baidu.com")

    async def parse(self, response: Response):
        self.logger.info(response.text[:100])

if __name__ == "__main__":
    MySpider().run(settings=SpiderSettings(project_name="my_spider", concurrency=5))
```

更多示例（装饰器、配置文件、CrawlerProcess）详见 [快速上手](quick_start.md)。

## 核心概念

| 概念 | 说明 | 文档 |
|------|------|------|
| Spider | Lite 轻量 / Classic 完整 | [Lite](features/lite_spider.md) / [Classic](features/spider.md) |
| Request | HTTP 请求封装，支持优先级、回调、代理 | [Request 详解](features/request.md) |
| Response | 响应封装，提供 xpath/css/json/urljoin | [Response 详解](features/response.md) |
| Item | 数据结构定义，配合 Pipeline 自动入库 | [Item 数据项](features/item.md) |
| Pipeline | 数据管道链，批量入库（Classic） | [Pipeline 管道](features/pipeline.md) |
| 中间件 | 下载器/爬虫/管道三层中间件（Classic） | [中间件系统](features/middleware.md) |
| 配置 | 代码 / 配置文件 / 环境变量 / YAML / TOML | [配置说明](features/settings.md) |
| 下载器 | aiohttp / httpx / playwright / patchright | [下载器](features/downloader.md) |

## 下一步

- [使用前必读](use/before_use.md) - 模式选择与项目结构
- [快速上手](quick_start.md) - 完整入门教程
- [Lite 轻量爬虫](features/lite_spider.md) - Lite 模式详解
- [Spider 进阶](features/spider.md) - Classic 模式详解
- [配置说明](features/settings.md) - 详细的配置选项
