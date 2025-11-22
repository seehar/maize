# 快速上手

## 创建第一个爬虫

> 以百度爬虫为例，实现一个最小的爬虫项目

### 最简单的示例

```python
from typing import Any, AsyncGenerator

from maize import Request, Response, Spider


class BaiduSpider(Spider):
    async def start_requests(self) -> AsyncGenerator[Request, Any]:
        yield Request(url="http://www.baidu.com")

    async def parse(self, response: Response):
        print(f"响应状态码: {response.status}")
        print(f"页面标题: {response.xpath('//title/text()').get()}")


if __name__ == '__main__':
    BaiduSpider().run()
```

### 使用 CrawlerProcess

如果需要更多控制，可以使用 `CrawlerProcess`：

```python
import asyncio
from typing import Any, AsyncGenerator

from maize import CrawlerProcess, Request, Response, Spider


class BaiduSpider(Spider):
    async def start_requests(self) -> AsyncGenerator[Request, Any]:
        yield Request(url="http://www.baidu.com")

    async def parse(self, response: Response):
        print(f"parse: {response}")


async def main():
    process = CrawlerProcess()
    await process.crawl(BaiduSpider)
    await process.start()


if __name__ == '__main__':
    asyncio.run(main())
```

## 下发新任务

`parse` 中支持下发新任务，只需要 `yield Request` 即可。

### 基本用法

```python
from typing import Any, AsyncGenerator

from maize import Request, Response, Spider


class MultiPageSpider(Spider):
    async def start_requests(self) -> AsyncGenerator[Request, Any]:
        yield Request(url="http://www.example.com")

    async def parse(self, response: Response):
        # 不指定 callback，任务会默认调度到 parse
        yield Request(url="http://www.example.com/page2")

        # 指定 callback，任务由 callback 指定的函数解析
        yield Request(url="http://www.example.com/detail", callback=self.parse_detail)

    async def parse_detail(self, response: Response):
        print(f"详情页: {response.url}")
```

### 批量下发任务

```python
async def parse(self, response: Response):
    # 解析列表页，提取详情页链接
    detail_urls = response.xpath('//a[@class="detail-link"]/@href').getall()

    for url in detail_urls:
        yield Request(
            url=response.urljoin(url),  # 自动拼接完整URL
            callback=self.parse_detail,
            priority=1  # 设置优先级
        )
```

## 爬虫配置

maize 提供了三种配置方式，优先级从高到低为：**代码配置 > 配置对象 > 配置文件**

### 方式一：使用 SpiderSettings 对象

推荐使用 `SpiderSettings` 对象进行配置，可以获得更好的代码提示：

```python
from maize import Spider, SpiderSettings


class MySpider(Spider):
    # ...爬虫实现...
    pass


if __name__ == "__main__":
    settings = SpiderSettings(
        project_name="我的爬虫",
        concurrency=10,  # 并发数
        log_level="DEBUG",  # 日志级别
        downloader="maize.HTTPXDownloader",  # 使用 HTTPX 下载器
    )

    # 配置请求相关参数
    settings.request.verify_ssl = False  # 不验证 SSL
    settings.request.request_timeout = 30  # 请求超时时间
    settings.request.max_retry_count = 3  # 最大重试次数

    MySpider().run(settings=settings)
```

### 方式二：使用配置文件

在项目根目录创建 `settings.py`：

```python
# settings.py
from maize import SpiderSettings


class Settings(SpiderSettings):
    project_name = "我的爬虫项目"
    concurrency = 10
    log_level = "INFO"
    downloader = "maize.AioHttpDownloader"

    # 也可以使用嵌套配置
    # request = RequestSettings(
    #     verify_ssl=False,
    #     request_timeout=30
    # )
```

在爬虫中引用配置文件：

```python
if __name__ == "__main__":
    # 默认加载 settings.Settings
    MySpider().run(settings_path="settings.Settings")
```

项目结构：

```text
my_project/
    ├── settings.py      # 配置文件
    ├── spider.py        # 爬虫文件
    └── run.py           # 启动文件
```

### 方式三：自定义配置（custom_settings）

在 Spider 类中使用 `custom_settings` 进行配置：

```python
class MySpider(Spider):
    custom_settings = {
        "concurrency": 5,
        "log_level": "DEBUG",
        "downloader": "maize.HTTPXDownloader",
    }

    # ...爬虫实现...
```

**注意**：`custom_settings` 优先级最高，会覆盖配置文件和 SpiderSettings 中的配置。

### 配置优先级

```
custom_settings > SpiderSettings 对象 > 配置文件 > 默认配置
```

## 提高采集速度

### 增加并发数

修改 `concurrency` 参数：

```python
settings = SpiderSettings(concurrency=20)  # 设置20个并发
```

### 使用请求优先级

为重要的请求设置更高的优先级：

```python
# 数值越大，优先级越高
yield Request(url="http://important.com", priority=10)
yield Request(url="http://normal.com", priority=1)
```

### 减少等待时间

```python
settings = SpiderSettings()
settings.request.request_timeout = 10  # 减少请求超时时间
```

## 选择下载器

maize 内置了多种下载器，可根据需求选择。

### 内置下载器

| 下载器                    | 说明                      | 适用场景        |
|:-----------------------|:------------------------|:------------|
| `AioHttpDownloader`    | 基于 aiohttp，默认下载器        | 一般网页采集      |
| `HTTPXDownloader`      | 基于 httpx，支持 HTTP/2       | 需要 HTTP/2 支持 |
| `PlaywrightDownloader` | 基于 Playwright，支持浏览器自动化 | 动态渲染页面、RPA  |
| `PatchrightDownloader` | 基于 Patchright，反检测能力更强   | 反爬虫较强的网站    |

### 配置下载器

```python
from maize import SpiderSettings

# 使用 AioHttp 下载器（默认）
settings = SpiderSettings(
    downloader="maize.AioHttpDownloader"
)

# 使用 HTTPX 下载器
settings = SpiderSettings(
    downloader="maize.HTTPXDownloader"
)

# 使用 Playwright 下载器（需要安装 maize[rpa]）
settings = SpiderSettings(
    downloader="maize.downloader.playwright_downloader.PlaywrightDownloader"
)
```

## 自定义下载器

继承 `BaseDownloader` 实现自定义下载器：

```python
import typing

from maize import BaseDownloader, Request, Response


class CustomDownloader(BaseDownloader):
    async def download(self, request: Request) -> typing.Optional[Response]:
        """
        执行实际的下载操作
        """
        # 实现下载逻辑
        pass

    @staticmethod
    def structure_response(
        request: Request,
        response: typing.Any,
        body: bytes
    ) -> Response:
        """
        将原始响应转换为 maize Response 对象
        """
        # 实现响应转换逻辑
        pass
```

在配置中使用自定义下载器：

```python
settings = SpiderSettings(
    downloader="your_module.CustomDownloader"
)
```

**建议**：始终继承 `BaseDownloader` 来实现自定义下载器，这样可以复用很多基础功能。

## 自定义日志模块

maize 默认使用 Python 的 `logging` 模块，但可以方便地替换为其他日志库，如 `loguru`。

### 使用 loguru

创建自定义日志处理器：

```python
# logger_util.py
import logging
import sys

from loguru import logger as loguru_logger


class InterceptHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.logger = loguru_logger
        self.logger.remove()
        self.logger.add(
            sys.stdout,
            level="DEBUG",
            format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                   "{process.name} | "
                   "{thread.name} | "
                   "<cyan>{module}</cyan>.<cyan>{function}</cyan>"
                   ":<cyan>{line}</cyan> | "
                   "<level>{level}</level>: "
                   "<level>{message}</level>",
        )

    def emit(self, record: logging.LogRecord):
        logger_opt = self.logger.opt(depth=6, exception=record.exc_info)
        logger_opt.log(record.levelname, record.getMessage())
```

在配置中指定日志处理器：

```python
# 使用 SpiderSettings
settings = SpiderSettings(
    logger_handler="your_module.logger_util.InterceptHandler"
)

# 或在 settings.py 中
class Settings(SpiderSettings):
    logger_handler = "your_module.logger_util.InterceptHandler"
```

## 数据提取

### 使用 XPath

```python
async def parse(self, response: Response):
    # 提取单个结果
    title = response.xpath('//title/text()').get()

    # 提取所有结果
    links = response.xpath('//a/@href').getall()

    # 链式调用
    items = response.xpath('//div[@class="item"]')
    for item in items:
        name = item.xpath('.//h3/text()').get()
        price = item.xpath('.//span[@class="price"]/text()').get()
```

### 使用 CSS 选择器

```python
async def parse(self, response: Response):
    # 提取单个结果
    title = response.css('title::text').get()

    # 提取所有结果
    links = response.css('a::attr(href)').getall()

    # 链式调用
    items = response.css('div.item')
    for item in items:
        name = item.css('h3::text').get()
        price = item.css('span.price::text').get()
```

### 使用正则表达式

```python
async def parse(self, response: Response):
    import re

    # 提取邮箱地址
    emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                        response.text)
```

### 解析 JSON

```python
async def parse(self, response: Response):
    data = response.json()
    items = data.get('items', [])
    for item in items:
        print(item['name'])
```

## 数据存储

### 使用 Item

定义 Item 结构：

```python
# items.py
from maize import Field, Item


class ProductItem(Item):
    __table_name__ = "products"  # 数据库表名

    name = Field()
    price = Field()
    url = Field()
```

在爬虫中使用：

```python
from items import ProductItem


class MySpider(Spider):
    async def parse(self, response: Response):
        item = ProductItem()
        item["name"] = response.xpath('//h1/text()').get()
        item["price"] = response.xpath('//span[@class="price"]/text()').get()
        item["url"] = response.url

        yield item  # 提交到数据管道处理
```

### 自定义 Pipeline

创建自定义数据管道：

```python
# pipelines.py
from typing import List

from maize import BasePipeline, Item


class CustomPipeline(BasePipeline):
    async def open(self):
        """管道初始化时调用"""
        print("Pipeline 已启动")

    async def close(self):
        """管道关闭时调用"""
        print("Pipeline 已关闭")

    async def process_item(self, items: List[Item]) -> bool:
        """
        处理数据
        返回 True 表示处理成功，False 表示失败（会重试）
        """
        for item in items:
            print(f"保存数据: {item.to_dict()}")
        return True

    async def process_error_item(self, items: List[Item]):
        """处理超过重试次数的数据"""
        for item in items:
            print(f"失败的数据: {item.to_dict()}")
```

在配置中注册：

```python
settings = SpiderSettings()
settings.pipeline.pipelines = [
    "your_module.pipelines.CustomPipeline"
]
```

## 错误处理

### 请求错误回调

```python
from maize import Request


class MySpider(Spider):
    async def start_requests(self):
        yield Request(
            url="http://example.com",
            callback=self.parse,
            error_callback=self.error_handler  # 指定错误回调
        )

    async def parse(self, response: Response):
        print(response.text)

    async def error_handler(self, request: Request):
        """处理请求失败的情况"""
        self.logger.error(f"请求失败: {request.url}")
        # 可以选择重新下发请求
        # yield Request(url=request.url)
```

### 设置重试次数

```python
settings = SpiderSettings()
settings.request.max_retry_count = 3  # 最大重试3次
```

## 下一步

- [Spider 进阶](features/spider.md) - 学习完整的项目结构
- [TaskSpider](features/task_spider.md) - 任务爬虫的使用
- [配置说明](features/settings.md) - 详细的配置选项
- [Request 详解](features/request.md) - 请求的高级用法
- [Response 详解](features/response.md) - 响应的处理方法
