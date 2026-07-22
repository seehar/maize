<div align="center">
  <img src="docs/assets/logo.svg" alt="Logo" width="200" height="200">
</div>

# maize

[![codecov](https://codecov.io/gh/seehar/maize/graph/badge.svg?token=ZG5ESDLPX6)](https://codecov.io/gh/seehar/maize)
![](https://img.shields.io/github/watchers/seehar/maize?style=social)
![](https://img.shields.io/github/stars/seehar/maize?style=social)
![](https://img.shields.io/github/forks/seehar/maize?style=social)
[![Downloads](https://pepy.tech/badge/maize)](https://pepy.tech/project/maize)
[![Downloads](https://pepy.tech/badge/maize/month)](https://pepy.tech/project/maize)
[![Downloads](https://pepy.tech/badge/maize/week)](https://pepy.tech/project/maize)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PyPI](https://img.shields.io/pypi/v/maize.svg)](https://pypi.org/project/maize/)

[文档](https://seehar.github.io/maize/) | [示例](examples/)

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

## 开发

安装预提交钩子：

```shell
pre-commit install
```

运行测试：

```shell
pytest --cov=./maize --cov-report=html
```

## License

MIT
