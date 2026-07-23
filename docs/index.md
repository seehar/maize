---
hide:
  - toc
---

# maize

> 基于 asyncio 的轻量级异步 Python 爬虫框架

**双模式设计**：Lite 单文件即跑，Classic 完整中间件/管道/调度器。

```python
from maize.aio.lite import LiteSpider, Request, Response

class MySpider(LiteSpider):
    async def start_requests(self):
        yield Request(url="https://example.com")

    async def parse(self, response: Response):
        self.logger.info(response.xpath("//title/text()").get())

if __name__ == "__main__":
    MySpider().run()  # 就这么简单
```

<div class="grid cards" markdown>

- :material-rocket-launch:{ .lg .middle } **快速开始**

    ---

    5 分钟写一个能跑的爬虫。Lite 模式无需配置文件。

    [:octicons-arrow-right-24: 快速上手](quick_start.md)

- :material-sitemap:{ .lg .middle } **架构概览**

    ---

    理解请求生命周期、组件关系、Lite vs Classic 数据流。

    [:octicons-arrow-right-24: 架构概览](architecture.md)

- :material-lightbulb-on:{ .lg .middle } **选择模式**

    ---

    Lite 还是 Classic？按场景选择。

    [:octicons-arrow-right-24: 使用前必读](use/before_use.md)

- :material-code-braces:{ .lg .middle } **示例代码**

    ---

    6 个完整示例：Lite、Classic、中间件、RPA、暂停继续。

    [:octicons-arrow-right-24: 示例索引](examples.md)

- :material-help-circle:{ .lg .middle } **FAQ**

    ---

    常见问题、安装报错、运行时异常、故障排查。

    [:octicons-arrow-right-24: FAQ](faq.md)

- :material-api:{ .lg .middle } **API Reference**

    ---

    自动生成的 API 文档，直接从源码 docstring 提取。

    [:octicons-arrow-right-24: API Reference](api_reference.md)

</div>

## 特性

- :material-lightning-bolt: **异步高性能** — 基于 asyncio 实现，全链路 async/await
- :material-scale-balance: **双模式** — Lite 轻量开箱即用，Classic 完整中间件/管道/调度器
- :material-layers-triple: **中间件系统** — 下载器/爬虫/管道三层中间件，可插拔扩展
- :material-download: **插件化下载器** — 内置 aiohttp、httpx、playwright、patchright
- :material-robot: **RPA 支持** — 浏览器自动化，动态页面采集与反检测
- :material-database: **数据管道** — 多管道并行，批量入库，支持 MySQL/Redis/CSV
- :material-server-network: **分布式支持** — 基于 Redis 实现分布式爬虫
- :material-pause: **暂停/继续** — 爬虫运行时暂停和恢复
- :material-cog: **灵活配置** — 代码、配置文件、环境变量、YAML/TOML 多方式配置

## 安装

```shell
pip install maize
```

可选依赖：

| 命令 | 说明 |
|------|------|
| `pip install maize[rpa]` | Playwright/Patchright 浏览器自动化 |
| `pip install maize[mysql]` | MySQL Pipeline 支持 |
| `pip install maize[redis]` | Redis 分布式支持 |
| `pip install maize[all]` | 完整安装 |

## 两种爬虫模式

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

## 环境要求

- Python 3.10+
- Linux, Windows, macOS

## 下一步

- [架构概览](architecture.md) - 理解框架结构
- [使用前必读](use/before_use.md) - 模式选择与项目结构
- [快速上手](quick_start.md) - 完整入门教程
- [示例索引](examples.md) - 完整代码示例
- [FAQ](faq.md) - 常见问题解答
- [更新日志](https://github.com/seehar/maize/blob/main/CHANGELOG.md) - 版本变更记录
