<div align="center">
  <img src="docs/assets/logo.svg" alt="Logo" width="200" height="200">
</div>

# maize

> 一个基于 asyncio 的轻量级异步 Python 爬虫框架

[![codecov](https://codecov.io/gh/seehar/maize/graph/badge.svg?token=ZG5ESDLPX6)](https://codecov.io/gh/seehar/maize)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PyPI](https://img.shields.io/pypi/v/maize.svg)](https://pypi.org/project/maize/)
[![License](https://img.shields.io/github/license/seehar/maize.svg)](LICENSE)
[![Downloads](https://pepy.tech/badge/maize)](https://pepy.tech/project/maize)

[文档](https://seehar.github.io/maize/) | [示例](examples/) | [更新日志](CHANGELOG.md) | [贡献指南](CONTRIBUTING.md)

---

## 为什么选择 maize

maize 是一个**双模式**的异步爬虫框架：

- **Lite 模式** —— 单文件即跑，构造函数即用，5 分钟上手。适合简单抓取、API 采集、监控轮询。
- **Classic 模式** —— 完整的中间件链、数据管道、分布式调度。适合大型项目、多管道入库、反爬场景。

如果你在 Scrapy 和"从零手写 aiohttp 脚本"之间犹豫，maize 给你第三条路：**比 Scrapy 轻，比裸 aiohttp 全**。

### 与 Scrapy 的对比

| 维度 | maize | Scrapy |
|------|-------|--------|
| 异步模型 | 原生 asyncio（全链路 async/await） | Twisted（可通过 `asyncio` 集成） |
| 轻量模式 | ✅ Lite 模式，单文件即跑 | ❌ 需 `startproject` 脚手架 |
| 下载器 | aiohttp / httpx / Playwright / Patchright | urllib3 / 需第三方 aiohttp |
| RPA 支持 | ✅ 内置 Playwright + Patchright（反检测） | 需 scrapy-playwright 插件 |
| 配置 | Pydantic v2 强类型，代码/文件/环境变量/YAML/TOML | dict 风格 settings.py |
| 中间件 | 三层（下载器/爬虫/管道） | 三层（同左） |
| 分布式 | 基于 Redis | 需 scrapy-redis |
| 体积 | 核心仅依赖 aiohttp + pydantic | Twisted + parsel + 更多 |

**适合 maize 的场景**：需要原生 asyncio、需要 RPA/浏览器自动化、想要 Pydantic 强类型配置、项目不大但未来可能扩展。

**适合 Scrapy 的场景**：需要成熟的生态和插件、团队已熟悉 Scrapy、需要 Twisted 生态集成。

## 特性

- **异步高性能** — 基于 asyncio 实现，全链路 async/await
- **双模式** — Lite 轻量开箱即用，Classic 完整中间件/管道/调度器
- **中间件系统** — 下载器/爬虫/管道三层中间件，可插拔扩展
- **插件化下载器** — 内置 aiohttp、httpx、playwright、patchright
- **RPA 支持** — 浏览器自动化，动态页面采集与反检测
- **数据管道** — 多管道并行，批量入库，支持 MySQL/Redis/CSV
- **分布式支持** — 基于 Redis 实现分布式爬虫
- **暂停/继续** — 爬虫运行时暂停和恢复
- **灵活配置** — 代码、配置文件、环境变量、YAML/TOML 多方式配置

## 目录

- [安装](#安装)
- [快速开始](#快速开始)
- [示例](#示例)
- [开发](#开发)
- [许可证](#许可证)

## 安装

```shell
pip install maize
```

可选依赖：

```shell
pip install maize[rpa]      # Playwright/Patchright 浏览器自动化
pip install maize[mysql]    # MySQL 支持
pip install maize[redis]    # Redis 分布式支持
pip install maize[all]      # 完整安装
```

## 快速开始

### Lite 爬虫（推荐入门）

无需配置文件，构造函数即用：

```python
from maize.aio.lite import LiteSpider, Request, Response

class MySpider(LiteSpider):
    async def start_requests(self):
        yield Request(url="https://example.com")

    async def parse(self, response: Response):
        self.logger.info(response.xpath("//title/text()").get())

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

完整文档请访问 [seehar.github.io/maize](https://seehar.github.io/maize/)

## 示例

仓库 `examples/` 目录包含多个完整示例：

| 示例 | 说明 |
|------|------|
| [`lite_spider_example.py`](examples/lite_spider_example.py) | Lite 爬虫基础用法 |
| [`simple_spider.py`](examples/simple_spider.py) | Classic 爬虫最简示例 |
| [`middleware_example.py`](examples/middleware_example.py) | 自定义中间件完整示例 |
| [`baidu_spider/`](examples/baidu_spider/) | 完整项目结构（Item + Pipeline + 多爬虫） |
| [`rpa_spdier/`](examples/rpa_spdier/) | RPA 浏览器自动化（百度/JD/下载/代理） |
| [`pause_and_proceed_spider/`](examples/pause_and_proceed_spider/) | 暂停和继续爬虫 |

## 开发

安装开发环境：

```shell
git clone https://github.com/seehar/maize.git
cd maize
uv sync --all-extras
uv run pre-commit install
```

运行测试：

```shell
uv run pytest --cov=./maize --cov-report=html
```

详见 [贡献指南](CONTRIBUTING.md)。

## 许可证

[MIT](LICENSE)

Copyright &copy; 2024-2026 seehar
