# Lite 轻量爬虫

Lite 爬虫是 maize 的轻量级解决方案，适用于简单场景，提供内置并发、重试和代理支持，无需中间件系统。

## 与 Classic Spider 的区别

| 特性 | Classic Spider | Lite Spider |
|------|----------------|-------------|
| 中间件 | 支持 | 不支持 |
| 管道 | 支持 | 不支持 |
| 调度器 | 支持 | 不支持 |
| 并发控制 | 可配置 | 可配置 |
| 重试机制 | 可配置 | 可配置 |
| 代理 | 可配置 | 可配置 |
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

### 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `concurrency` | `int` | `5` | 最大并发请求数 |
| `retry` | `int` | `3` | 请求失败重试次数 |
| `proxy` | `str \| None` | `None` | 代理地址 |
| `timeout` | `float` | `30.0` | 请求超时时间（秒） |

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

## 错误处理

LiteSpider 会自动处理请求失败，按照 `retry` 次数自动重试：

```python
class ErrorHandlingSpider(LiteSpider):
    retry = 5  # 增加重试次数

    async def start_requests(self):
        yield Request(url="https://unstable-example.com")

    async def parse(self, response: Response):
        if response.status == 200:
            print(f"成功: {response.url}")
        else:
            print(f"失败: {response.status}")
```

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
