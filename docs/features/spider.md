# Spider 进阶

## 项目结构

一个完整的爬虫项目需要将不同功能模块拆分出来，各司其职，便于开发和维护。

### 推荐的项目结构

```text
my_project/
├── spiders/               # 存放所有爬虫
│   ├── __init__.py
│   ├── spider_1.py
│   ├── spider_2.py
│   └── ...
├── items.py              # 定义爬虫解析后的 Item
├── pipelines.py          # 自定义数据管道（可选）
├── settings.py           # 项目配置文件
└── run.py                # 启动入口
```

### 完整示例项目

下面以百度爬虫为例，展示一个完整的爬虫项目。

#### 项目目录结构

```text
baidu_spider/
├── spiders/
│   ├── __init__.py
│   └── baidu_spider.py
├── items.py
├── pipelines.py          # 可选
├── settings.py
└── run.py
```

#### 1. 定义 Item（items.py）

```python
from maize import Field, Item


class BaiduItem(Item):
    __table_name__ = "baidu_hot_search"  # 数据库表名（如果使用 MySQL Pipeline）

    title = Field()
    url = Field()
    rank = Field()
```

#### 2. 编写爬虫（spiders/baidu_spider.py）

```python
from typing import Any, AsyncGenerator

from maize import Request, Response, Spider
from baidu_spider.items import BaiduItem


class BaiduSpider(Spider):
    async def start_requests(self) -> AsyncGenerator[Request, Any]:
        """生成初始请求"""
        yield Request(url="http://www.baidu.com")

    async def parse(self, response: Response):
        """解析首页，提取热搜列表"""
        self.logger.info(f"正在解析: {response.url}")

        # 提取热搜列表
        li_list = response.xpath("//li[contains(@class, 'hotsearch-item')]")

        for index, li in enumerate(li_list, start=1):
            item = BaiduItem()
            item["title"] = li.xpath(".//span[@class='title-content-title']/text()").get()
            item["url"] = li.xpath("./a/@href").get()
            item["rank"] = index
            yield item

        # 继续爬取其他页面
        for i in range(5):
            url = f"http://www.baidu.com/page/{i}"
            yield Request(url=url, callback=self.parse_page)

    async def parse_page(self, response: Response):
        """解析列表页"""
        self.logger.info(f"正在解析列表页: {response.url}")

        # 提取详情页链接
        detail_urls = response.xpath('//a[@class="detail"]/@href').getall()

        for url in detail_urls:
            yield Request(
                url=response.urljoin(url),
                callback=self.parse_detail,
                priority=1  # 设置优先级
            )

    async def parse_detail(self, response: Response):
        """解析详情页"""
        self.logger.info(f"正在解析详情页: {response.url}")

        item = BaiduItem()
        item["title"] = response.xpath('//h1/text()').get()
        item["url"] = response.url
        yield item
```

#### 3. 配置文件（settings.py）

```python
from maize import SpiderSettings


class Settings(SpiderSettings):
    # 基础配置
    project_name = "百度爬虫"
    concurrency = 5  # 并发数
    log_level = "INFO"  # 日志级别

    # 下载器配置
    downloader = "maize.HTTPXDownloader"

    # 请求配置（可选）
    # request = RequestSettings(
    #     verify_ssl=False,
    #     request_timeout=30,
    #     max_retry_count=3,
    #     random_wait_time=(1, 3)  # 随机等待1-3秒
    # )

    # 数据管道配置（可选）
    # pipeline = PipelineSettings(
    #     pipelines=["baidu_spider.pipelines.CustomPipeline"],
    #     handle_batch_max_size=100
    # )

    # MySQL 配置（如果使用 MySQL Pipeline）
    # mysql = MySQLSettings(
    #     host="localhost",
    #     port=3306,
    #     db="spider_db",
    #     user="root",
    #     password="password"
    # )
```

#### 4. 启动文件（run.py）

```python
import asyncio

from maize import CrawlerProcess
from baidu_spider.spiders.baidu_spider import BaiduSpider


async def main():
    process = CrawlerProcess()
    await process.crawl(BaiduSpider)
    await process.start()


if __name__ == "__main__":
    asyncio.run(main())
```

## Spider 核心方法

### start_requests()

生成初始请求，必须实现的方法。

```python
from typing import Any, AsyncGenerator

from maize import Request, Spider


class MySpider(Spider):
    async def start_requests(self) -> AsyncGenerator[Request, Any]:
        """生成初始请求"""
        urls = [
            "http://www.example.com/page1",
            "http://www.example.com/page2",
            "http://www.example.com/page3",
        ]

        for url in urls:
            yield Request(url=url)
```

### parse()

默认的解析方法，处理响应数据。

```python
from maize import Response, Spider


class MySpider(Spider):
    async def parse(self, response: Response):
        """解析响应"""
        # 提取数据
        title = response.xpath('//title/text()').get()

        # 下发新请求
        yield Request(url="http://www.example.com/next", callback=self.parse_next)

        # 提交数据
        yield {"title": title, "url": response.url}
```

### 自定义解析方法

可以定义多个解析方法来处理不同类型的页面：

```python
class MySpider(Spider):
    async def start_requests(self):
        yield Request(url="http://www.example.com", callback=self.parse_list)

    async def parse_list(self, response: Response):
        """解析列表页"""
        links = response.xpath('//a[@class="item"]/@href').getall()
        for link in links:
            yield Request(
                url=response.urljoin(link),
                callback=self.parse_detail
            )

    async def parse_detail(self, response: Response):
        """解析详情页"""
        item = {
            'title': response.xpath('//h1/text()').get(),
            'content': response.xpath('//div[@class="content"]/text()').get(),
        }
        yield item
```

## 使用 meta 传递数据

在不同的解析函数之间传递数据：

```python
class MySpider(Spider):
    async def parse(self, response: Response):
        """解析列表页"""
        items = response.xpath('//div[@class="item"]')

        for item in items:
            title = item.xpath('.//h3/text()').get()
            detail_url = item.xpath('.//a/@href').get()

            # 通过 meta 传递数据
            yield Request(
                url=response.urljoin(detail_url),
                callback=self.parse_detail,
                meta={'title': title}  # 传递标题
            )

    async def parse_detail(self, response: Response):
        """解析详情页"""
        # 从 meta 中获取数据
        title = response.request.meta.get('title')
        content = response.xpath('//div[@class="content"]/text()').get()

        yield {
            'title': title,
            'content': content,
            'url': response.url
        }
```

## 设置请求优先级

通过 `priority` 参数控制请求的处理顺序：

```python
class MySpider(Spider):
    async def parse(self, response: Response):
        # 重要请求，优先级高
        yield Request(
            url="http://www.example.com/important",
            callback=self.parse_important,
            priority=10  # 数值越大，优先级越高
        )

        # 普通请求
        yield Request(
            url="http://www.example.com/normal",
            priority=1
        )
```

## 处理请求错误

为请求设置错误回调函数：

```python
from maize import Request, Response, Spider


class MySpider(Spider):
    async def start_requests(self):
        yield Request(
            url="http://www.example.com",
            callback=self.parse,
            error_callback=self.handle_error  # 设置错误回调
        )

    async def parse(self, response: Response):
        print(response.text)

    async def handle_error(self, request: Request):
        """处理请求失败"""
        self.logger.error(f"请求失败: {request.url}")

        # 可以选择重新下发请求
        if request.current_retry_count < 3:
            yield Request(
                url=request.url,
                callback=self.parse,
                error_callback=self.handle_error
            )
```

## 使用 custom_settings

在 Spider 类中使用 `custom_settings` 进行个性化配置：

```python
class MySpider(Spider):
    custom_settings = {
        "concurrency": 10,
        "log_level": "DEBUG",
        "downloader": "maize.HTTPXDownloader",
        "request": {
            "verify_ssl": False,
            "request_timeout": 30,
            "max_retry_count": 3,
        }
    }

    async def start_requests(self):
        yield Request(url="http://www.example.com")

    async def parse(self, response: Response):
        print(response.text)
```

## 爬虫生命周期

Spider 提供了生命周期钩子函数：

```python
from maize import Spider, SpiderSettings


class MySpider(Spider):
    async def open(self, settings: SpiderSettings):
        """
        爬虫启动时调用
        可以在这里进行初始化操作
        """
        await super().open(settings)  # 必须调用父类方法
        self.logger.info("爬虫启动")
        # 初始化数据库连接等

    async def close(self):
        """
        爬虫关闭时调用
        可以在这里进行清理操作
        """
        self.logger.info("爬虫关闭")
        # 关闭数据库连接等
        await super().close()  # 必须调用父类方法

    async def start_requests(self):
        yield Request(url="http://www.example.com")

    async def parse(self, response: Response):
        print(response.text)
```

## 暂停和继续爬虫

maize 支持暂停和继续爬虫的功能：

```python
class MySpider(Spider):
    async def parse(self, response: Response):
        # 处理数据...

        # 在某个条件下暂停爬虫
        if some_condition:
            await self.pause_spider()  # 暂停所有请求
            self.logger.info("爬虫已暂停")

        # 或者只暂停低优先级的请求
        if another_condition:
            await self.pause_spider(lte_priority=5)  # 只暂停优先级 <= 5 的请求

    async def other_parse(self, response: Response):
        # 在某个条件下继续爬虫
        if resume_condition:
            await self.proceed_spider()  # 继续所有请求
            self.logger.info("爬虫已继续")

        # 或者只继续高优先级的请求
        if another_resume_condition:
            await self.proceed_spider(gte_priority=5)  # 只继续优先级 >= 5 的请求
```

更多详细示例请参考：[暂停和继续示例](../examples/pause_and_proceed_spider/)

## 下一步

- [TaskSpider](task_spider.md) - 任务爬虫的使用
- [配置说明](settings.md) - 详细的配置选项
- [Request 详解](request.md) - 请求的高级用法
- [Response 详解](response.md) - 响应的处理方法
- [Pipeline 管道](pipeline.md) - 数据管道使用
