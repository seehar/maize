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
| 优先级调度 | 支持 | 支持（PriorityQueue） |
| 默认 UA | 可配置 | 内置 `default_headers` |
| 运行时统计 | 支持 | 内置 `crawler.stats` |
| 优雅关闭 | 支持 | 支持（SIGINT/SIGTERM） |
| 域名级并发限流 | 支持 | 内置 `per_domain_concurrency` |
| 自定义重试策略 | 支持 | 内置 `should_retry` |
| 结构化请求日志 | 支持 | 内置（key=value 格式） |
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
| `per_domain_concurrency` | `int` | `0` | 单域名最大并发数，0 表示不限。按 URL 的 netloc 分组限流 |
| `default_headers` | `dict[str, str]` | `{"User-Agent": "maize-lite/1.0"}` | 默认请求头，在 `open()` 时合入 ClientSession。子类可重写以定制 UA、Accept 等 |

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

## 请求优先级

`Request(priority=N)` 按 priority 升序出队（数值越小越优先）。LiteSpider 内部使用 `asyncio.PriorityQueue`，
同 priority 的请求按入队顺序出队（tie-breaker 保证不触发 `Request` 比较）。

```python
class PrioritySpider(LiteSpider):
    async def start_requests(self):
        # 先抓详情页，再抓列表页
        yield Request(url="https://example.com/detail", priority=1)
        yield Request(url="https://example.com/list", priority=10)
```

## 默认请求头

LiteSpider 内置默认 UA `maize-lite/1.0`，避免 aiohttp 默认 UA 被站点拦截。
子类可重写 `default_headers` 属性定制：

```python
class CustomHeaderSpider(LiteSpider):
    @property
    def default_headers(self) -> dict[str, str]:
        return {
            "User-Agent": "my-spider/2.0",
            "Accept": "application/json",
        }
```

per-request 的 `Request.headers` 仍优先于 session 级 headers。

## 运行时统计

`LiteCrawler.stats` 提供运行时统计，`crawl()` 结束时自动输出汇总日志：

```python
crawler = LiteCrawler(spider)
await crawler.crawl()
print(crawler.stats)
# {'requested': 10, 'succeeded': 8, 'failed': 2, 'retried': 1, 'dropped': 3, 'items': 8}
```

| 指标 | 说明 |
|------|------|
| `requested` | 入队请求数（不含重试，重试单独计入 `retried`） |
| `succeeded` | status 在 1xx-3xx 的响应数 |
| `failed` | status==0 或 status>=400 的响应数 |
| `retried` | 触发重试的次数 |
| `dropped` | 被去重或深度控制丢弃的请求数 |
| `items` | 收集到的 Item 数 |

## 优雅关闭

`run()` 方法注册了 SIGINT/SIGTERM 信号处理。收到信号后：

1. 停止从 `start_requests` 拉取新请求
2. 等待当前 in-flight 请求处理完毕
3. 执行 `on_close` 钩子清理资源
4. 输出统计汇总

```python
class MySpider(LiteSpider):
    async def on_close(self) -> None:
        """Ctrl+C 时也会被调用，保证资源清理"""
        await self.db.close()

    ...
```

Windows 不支持 `loop.add_signal_handler`，降级走 `KeyboardInterrupt` 兜底，`on_close` 仍会执行。

## 错误处理与自定义重试

LiteSpider 会自动处理请求失败，按照 `retry` 次数自动重试。
默认对 status==0（连接失败）、status>=500（服务端错误）、status==429（限流）重试，
每次重试前递增指数退避延迟（1s, 2s, 4s...）。

### 增加重试次数

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

### 自定义重试策略

重写 `should_retry` 方法自定义哪些状态码需要重试：

```python
class CustomRetrySpider(LiteSpider):
    def should_retry(self, response: Response) -> bool:
        # 对 403（反爬）也重试
        if response.status == 403:
            return True
        # 对 408（超时）重试
        if response.status == 408:
            return True
        # 继承默认逻辑：0 / 5xx / 429
        return super().should_retry(response)
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

## 域名级并发限流

通过 `per_domain_concurrency` 限制单域名并发数，防止对单一站点请求过密：

```python
class PoliteSpider(LiteSpider):
    per_domain_concurrency = 1  # 单域名串行抓取

    async def start_requests(self):
        # a.com 的两个请求串行执行
        yield Request(url="https://a.com/1")
        yield Request(url="https://a.com/2")
        # b.com 可与 a.com 并行
        yield Request(url="https://b.com/1")
```

`per_domain_concurrency=0`（默认）表示不限，回退到全局 `concurrency`。按请求 URL 的 netloc 分组限流。注意：重试退避等待期间 semaphore 仍被持有，同域名其他请求会等待退避完成，对被限流的站点这属于礼貌行为。

## 结构化请求日志

LiteCrawler 输出 key=value 格式的结构化日志，便于 grep 和日志分析：

```
INFO  request url=https://example.com/page status=200 elapsed=0.35s retry=0
WARN  retry url=https://example.com/page attempt=1/3 status=500 delay=1s
ERROR fetch_failed url=https://example.com/page elapsed=3.20s retry=2 error=TimeoutError
ERROR parse_failed url=https://example.com/page status=200 elapsed=0.35s error=KeyError
```

日志级别：成功 → INFO，重试 → WARNING，失败 → ERROR。

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
