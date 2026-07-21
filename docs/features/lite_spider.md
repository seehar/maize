# Lite 轻量爬虫

Lite 爬虫是 maize 的轻量级解决方案，适用于简单场景，提供内置并发、重试和代理支持，无需中间件系统。

## 与 Classic Spider 的区别

| 特性 | Classic Spider | Lite Spider |
|------|----------------|-------------|
| 中间件 | 支持 | 不支持 |
| 管道 | 支持 | 仅 `process_item` 钩子 |
| 调度器 | 支持 | 不支持 |
| 并发控制 | 可配置 | 可配置 |
| 重试机制 | 可配置 | 可配置 |
| 代理 | 可配置 | 可配置 |
| 请求去重 | 支持（中间件） | 内置（可关闭） |
| 深度控制 | 支持（中间件） | 内置 `max_depth` |
| 回调路由 | 支持 | 支持 `Request(callback=...)` |
| 复杂度 | 高 | 低 |

## 快速开始

```python
from maize.aio.lite import LiteSpider, Request, Response


class MySpider(LiteSpider):
    async def start_requests(self):
        yield Request(url="https://example.com")

    async def parse(self, response: Response):
        print(response.text[:100])


if __name__ == "__main__":
    MySpider().run()
```

## 配置参数

LiteSpider 支持通过构造函数参数配置：

```python
class MySpider(LiteSpider):
    def __init__(self):
        super().__init__(
            concurrency=5,      # 并发数，默认 5
            retry=3,            # 重试次数，默认 3
            proxy="http://127.0.0.1:7890",  # 代理，默认 None
            timeout=30.0,       # 请求超时，默认 30 秒
        )
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `concurrency` | `int` | `5` | 最大并发请求数 |
| `retry` | `int` | `3` | 请求失败重试次数 |
| `proxy` | `str \| None` | `None` | 代理地址 |
| `timeout` | `float` | `30.0` | 请求超时时间（秒） |

### 可重写属性

除构造函数参数外，LiteSpider 还提供以下可重写属性：

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `max_depth` | `int` | `0` | 最大爬取深度，0 表示不限。start_requests 产出的请求为 depth=0，parse 中 yield 的 Request 每跟进一层 depth+1 |
| `dedup` | `bool` | `True` | 是否启用请求去重。设为 False 适合轮询采集、监控变化等重复抓取场景 |

### 数据处理钩子

`process_item` 是 LiteSpider 的数据处理扩展点，在 parse 中 yield Item 后自动调用：

```python
class MySpider(LiteSpider):
    async def process_item(self, item: Item) -> None:
        """重写以实现数据落盘"""
        # 写文件、写数据库等
        ...

    async def start_requests(self):
        ...

    async def parse(self, response):
        yield Item(...)
```

默认空实现，Item 仍会保留在 `crawler.items` 中。无需引入完整 pipeline 链即可实现数据落盘。

## 完整示例

```python
from maize.aio.lite import LiteSpider, Request, Response


class ExampleSpider(LiteSpider):
    """带配置的完整示例"""

    def __init__(self):
        super().__init__(
            concurrency=10,
            retry=3,
            proxy="http://127.0.0.1:7890",
            timeout=30.0,
        )

    async def start_requests(self):
        urls = [
            "https://example.com/page/1",
            "https://example.com/page/2",
            "https://example.com/page/3",
        ]
        for url in urls:
            yield Request(url=url)

    async def parse(self, response: Response):
        title = response.xpath("//title/text()").get()
        print(f"URL: {response.url}, Title: {title}")


if __name__ == "__main__":
    ExampleSpider().run()
```

## 生命周期钩子

可选的钩子方法，用于初始化和清理：

```python
class MySpider(LiteSpider):
    async def on_start(self) -> None:
        """爬虫启动前调用"""
        print("爬虫开始运行")

    async def on_close(self) -> None:
        """爬虫关闭后调用"""
        print("爬虫已关闭")

    async def start_requests(self):
        yield Request(url="https://example.com")

    async def parse(self, response: Response):
        print(response.text)
```

## 使用代理

通过 `proxy` 属性设置代理：

```python
class ProxySpider(LiteSpider):
    proxy = "http://user:password@127.0.0.1:7890"

    async def start_requests(self):
        yield Request(url="https://example.com")

    async def parse(self, response: Response):
        print(response.text)
```

## 请求去重

LiteSpider 默认启用请求去重，基于请求的 method+url+params+data 计算 hash 去重，
避免递归爬取时重复抓取同一 URL。

### 全局关闭去重

适合轮询采集、监控变化等需要重复抓取同一 URL 的场景：

```python
class PollingSpider(LiteSpider):
    dedup = False  # 整个 spider 不去重
```

### 单请求跳过去重

大部分去重，个别请求需要重复抓取时，通过 `Request(meta={"dont_filter": True})` 跳过：

```python
class MonitorSpider(LiteSpider):
    async def start_requests(self):
        yield Request(url="https://example.com/once")  # 去重
        yield Request(url="https://example.com/poll",
                      meta={"dont_filter": True})      # 重复抓
```

## 深度控制

通过 `max_depth` 限制递归爬取深度，防止爬虫无限递归：

```python
class BoundedSpider(LiteSpider):
    max_depth = 2  # 最多爬到 depth=2

    async def start_requests(self):
        yield Request(url="https://example.com/entry")  # depth=0

    async def parse(self, response):
        yield Request(url="https://example.com/next")   # depth=1
```

`max_depth=0`（默认）表示不限深度。

## 错误处理

LiteSpider 会自动处理请求失败，按照 `retry` 次数自动重试：

```python
class ErrorHandlingSpider(LiteSpider):
    retry = 5  # 增加重试次数

    async def start_requests(self):
        yield Request(url="https://unstable-example.com")

    async def parse(self, response):
        if response.status == 200:
            print(f"成功: {response.url}")
        else:
            print(f"失败: {response.status}")
```

## 自定义回调

通过 `Request(callback=...)` 路由到不同的解析方法，而非默认的 `parse`：

```python
class MultiCallbackSpider(LiteSpider):
    async def start_requests(self):
        yield Request(url="https://example.com/list",
                      callback=self.parse_detail)

    async def parse(self, response):
        """默认回调"""
        ...

    async def parse_detail(self, response):
        """自定义回调"""
        ...
```

callback 必须是 async 函数，接受 Response 参数，返回 async generator 或 coroutine（与 parse 契约一致）。

## 高级用法

如需更精细的控制，可以直接使用 `LiteCrawler`：

```python
import asyncio
from maize.aio.lite import LiteSpider, LiteCrawler, Request, Response


class MySpider(LiteSpider):
    async def start_requests(self):
        yield Request(url="https://example.com")

    async def parse(self, response: Response):
        print(response.text)


async def main():
    spider = MySpider()
    crawler = LiteCrawler(spider, concurrency=20)
    await crawler.crawl()


if __name__ == "__main__":
    asyncio.run(main())
```

## 下一步

- [Spider 进阶](spider.md) - Classic Spider 高级特性
- [Request 详解](request.md) - 请求参数说明
- [Response 详解](response.md) - 响应处理方法
