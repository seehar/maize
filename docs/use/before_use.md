# 使用前必读

## 选择爬虫模式

maize 提供两种爬虫模式，按需求选择：

| 场景 | 推荐模式 | 原因 |
|------|----------|------|
| 简单页面抓取、API 采集 | Lite | 轻量，无需中间件/管道，构造函数即用 |
| 监控轮询、定时抓取 | Lite | 内置去重可关闭，`dont_filter` 单请求逃生口 |
| 需要中间件（UA 轮换、代理池、重试策略） | Classic | 完整中间件链 |
| 多管道批量入库（MySQL + Redis + CSV） | Classic | Pipeline 链，批量处理 |
| 分布式爬虫 | Classic | 基于 Redis 的分布式调度 |
| RPA / 浏览器渲染页面 | Classic | Playwright/Patchright 下载器 |
| 快速原型、教学演示 | Lite | 5 分钟上手，单文件即跑 |

- **Lite 模式**：`from maize.aio.lite import LiteSpider`，详见 [Lite 轻量爬虫](../features/lite_spider.md)
- **Classic 模式**：`from maize import Spider`，详见 [Spider 进阶](../features/spider.md)

## 推荐项目结构

### Lite 项目（简单场景）

```text
my_project/
├── spider.py        # 爬虫文件（含 LiteSpider 子类）
└── run.py           # 启动入口（可选，也可直接在 spider.py 末尾 run）
```

最小示例（单文件即可运行）：

```python
# spider.py
from maize.aio.lite import LiteSpider, Request, Response

class MySpider(LiteSpider):
    async def start_requests(self):
        yield Request(url="https://example.com")

    async def parse(self, response: Response):
        self.logger.info(response.xpath("//title/text()").get())

if __name__ == "__main__":
    MySpider().run()
```

### Classic 项目（完整功能）

```text
my_project/
├── spiders/               # 存放所有爬虫
│   ├── __init__.py
│   ├── spider_1.py
│   └── spider_2.py
├── items.py              # 定义采集后的 Item
├── pipelines.py          # 自定义数据管道（可选）
├── middlewares.py        # 自定义中间件（可选）
├── settings.py           # 项目配置文件
└── run.py                # 启动入口
```

完整项目结构示例见 [Spider 进阶](../features/spider.md)。

## 模块对照表

| 功能 | Lite | Classic |
|------|------|---------|
| 爬虫基类 | `LiteSpider` | `Spider` / `TaskSpider` |
| 请求/响应 | `maize.common.http.Request/Response`（共享） | 同左 |
| 数据项 | `maize.common.items.Item`（共享） | 同左 |
| 配置 | 构造函数参数 + 可重写属性 | `SpiderSettings`（文件/对象/环境变量） |
| 并发控制 | `concurrency` 参数 | `SpiderSettings.concurrency` |
| 重试 | `retry` 参数 + `should_retry` | `RequestSettings.max_retry_count` + 中间件 |
| 代理 | `proxy` 参数 | `ProxySettings` 或 `Request.proxy` |
| 去重 | 内置 `dedup` 属性 | `DepthMiddleware` 等中间件 |
| 深度控制 | `max_depth` 属性 | `DepthMiddleware` |
| 数据处理 | `process_item` 钩子 | `Pipeline` 链 |
| 下载器 | aiohttp（内置） | 可选 aiohttp/httpx/playwright/patchright |
| 中间件 | 不支持 | 三层中间件链 |
| 日志 | `self.logger` | `self.logger` + `logger_handler` 配置 |
