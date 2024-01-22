# Item

解析响应后，需要返回 `Item` 类型的数据，触发数据自动入库。
自定义的 `Item` 需要继承 `maize` 的 `Item` 类，字段定义为 `Field`。示例：

```python
from maize import Field, Item


class BaiduItem(Item):
    url = Field()
    title = Field()
```

在 `Spider` 的 `parse` 中

```python
from maize import Spider


class BaiduSpider(Spider):
    start_urls = ["http://www.baidu.com"]

    async def parse(self, response):
        # 解析或处理 response
        item = BaiduItem()
        item["url"] = "https://www.baidu.com"
        item["title"] = "百度一下"
        yield item
```
