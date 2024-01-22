# 快速上手

## 创建 spider

> 以百度爬虫为例，实现一个最小的爬虫项目

```python
import asyncio
from maize import CrawlerProcess, Spider


class BaiduSpider(Spider):
    start_urls = ["http://www.baidu.com"]

    async def parse(self, response):
        print(f"parse: {response}")


async def run():
    process = CrawlerProcess()
    await process.crawl(BaiduSpider)
    await process.start()


if __name__ == '__main__':
    asyncio.run(run())
```


## 下发新任务

`parse` 中支持下发新任务，只需要 `yield Request` 即可。示例如下

```python
from maize import Request

async def parse(self, response):
    yield Request(url="url")  # 不指定 callback，任务会默认调度到 parse 上
    yield Request(url="url", callback=self.parse_page)  # 指定 callback，任务由 callback 指定的函数解析。注意，需要异步函数
```


## 爬虫配置

爬虫配置支持自定义配置或引入配置文件setting.py的方式。
配置文件：在工作区间的根目录下引入setting.py，具体参考默认配置文件

```text
spider
    baidu_spider.py
    ...
settings.py  # 默认情况下配置文件需与 run.py 同级别
run.py
```

自定义配置：使用类变量 `custom_settings`

```python
class BaiduSpider(Spider):
    custom_settings = {  # 自定义配置
        "CONCURRENCY": 1,  # 并发数
    }
```

配置优先级：自定义配置 > 配置文件，即自定义配置会覆盖配置文件里的配置信息，不过自定义配置只对自己有效，配置文件可以是多个爬虫公用的


## 加快采集

修改配置文件中的并发数 `CONCURRENCY` 即可


## 自定义下载器

内置基于 `aiohttp` 和 `httpx` 的两种下载器。可以很方便的在配置文件中修改

```python
DOWNLOADER = "maize.AioHttpDownloader"  # 基于 aiohttp 的下载器
DOWNLOADER = "maize.HTTPXDownloader"    # 基于 httpx 的下载器
```

下载器是插拔式的设计，您可以很容易替换为自定义的下载器。继承 `BaseDownloader` 实现 `download` 和 `structure_response` 两个方法。
将配置文件中的 `DOWNLOADER` 的路径替换为您自定义下载器的路径。示例：

```python
import typing

from maize import BaseDownloader, Request, Response


class CustomDownloader(BaseDownloader):

    async def download(self, request: Request) -> typing.Optional[Response]:
        pass
    
    @staticmethod
    def structure_response(request: Request, response: typing.Any, body: bytes) -> Response:
        pass
```

您也可以不继承 `BaseDownloader`，需要在自定义下载器中实现这几个方法：`fetch`, `download`, `create_instance`, `close`, `idle`。
但是我们建议您继承 `BaeDownloader` 来实现自定义下载器


## 自定义日志模块

`maize` 的日志默认使用 `Python` 自带的 `logging` 模块。
但是您可以很方便的替换为您想用的日志模块，比如 `loguru`。示例：

```python
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
            format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "  # 颜色>时间
            "{process.name} | "  # 进程名
            "{thread.name} | "  # 进程名
            "<cyan>{module}</cyan>.<cyan>{function}</cyan>"  # 模块名.方法名
            ":<cyan>{line}</cyan> | "  # 行号
            "<level>{level}</level>: "  # 等级
            "<level>{message}</level>",  # 日志内容
        )

    def emit(self, record: logging.LogRecord):
        logger_opt = self.logger.opt(depth=7, exception=record.exc_info)
        logger_opt.log(record.levelno, record.getMessage())
```

在配置文件中指定您的日志模块

```python
LOGGER_HANDLER = "the.logger.path.InterceptHandler"  # 请替换为实际路径
```
