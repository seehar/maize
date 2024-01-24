# Spider 进阶

## 项目结构

一个完整的爬虫项目，不可能是单文件爬虫，需要将不同功能模块拆分出来，各司其职，便于开发和维护。
推荐使用的项目结构

```text
├─example_spider
│ └─spiders        # 存放所有爬虫
│   ├─spiders_1.py
│   ├─spiders_2.py
│   └─...
├─items.py         # 定义爬虫解析后的 Item
├─settings.py      # 项目配置文件
└─run.py           # 启动入口，main.py 也可以
```

下面以百度爬虫为例，写一个完整的爬虫项目。目录结构：

```text
├─baidu_spider
│ └─spiders        # 存放所有爬虫
│   └─baidu_spider.py
├─items.py         # 定义爬虫解析后的 Item
├─settings.py      # 项目配置文件
└─run.py           # 启动入口，main.py 也可以
```

=== "baidu_spider.py"
    ```python
    from maize import Request
    from maize import Spider
    from baidu_spider.items import BaiduItem
    
    
    class BaiduSpider(Spider):
        start_urls = ["http://www.baidu.com", "http://www.baidu.com"]
    
        async def parse(self, response):
            print(f"parse: {response}")
            for i in range(1):
                url = "http://www.baidu.com"
                yield Request(url=url, callback=self.parse_page)
    
        async def parse_page(self, response):
            print(f"parse_page: {response}")
            for i in range(1):
                url = "http://www.baidu.com"
                yield Request(url=url, callback=self.parse_detail)
    
        async def parse_detail(self, response):
            # print(response.text)
            print(f"parse_detail: {response}")
            item = BaiduItem()
            item["url"] = "https://www.baidu.com"
            item["title"] = "百度一下"
            yield item
    ```

=== "items.py"
    ```python
    from maize import Field
    from maize import Item
    
    
    class BaiduItem(Item):
        url = Field()
        title = Field()
    ```

=== "settings.py"
    ```python
    PROJECT_NAME = "baidu_spider"
    CONCURRENCY = 1
    LOG_LEVEL = "DEBUG"
    ```

=== "run.py"
    ```python
    import asyncio
    
    from maize import CrawlerProcess
    from maize.utils import get_settings
    from baidu_spider.spiders.baidu_spider import BaiduSpider
    
    
    async def run():
        settings = get_settings("settings")
        process = CrawlerProcess(settings)
        await process.crawl(BaiduSpider)
        await process.start()
    
    
    if __name__ == '__main__':
        asyncio.run(run())
    ```
