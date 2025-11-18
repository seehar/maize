# Item

解析响应后，需要返回 `Item` 类型的数据，触发数据自动入库。
自定义的 `Item` 需要继承 `maize` 的 `Item` 类，字段定义为 `Field`。示例：

```python
from maize import Field, Item


class BaiduItem(Item):
    #  __table_name__ = "table_name"  # 表名，自动入库时必须设置
    url: str = Field()
    title: str = Field(default="默认标题")
```

在 `Spider` 的 `parse` 中

```python
from typing import Any, AsyncGenerator

from maize import Request, Response, Spider


class BaiduSpider(Spider):
    async def start_requests(self) -> AsyncGenerator[Request, Any]:
        yield Request(url="http://www.baidu.com")

    async def parse(self, response: Response):
        # 解析或处理 response
        item = BaiduItem()
        item["url"] = "https://www.baidu.com"
        item["title"] = "百度一下"
        yield item
```

## 使用方式

### 像字典一样使用

```python
item = BaiduItem()
item["url"] = "https://www.baidu.com"
item["title"] = "百度一下"
print(item["url"])
print(item["title"])
```


### 像属性一样使用

```python
item = BaiduItem()
item.url = "https://www.baidu.com"
item.title = "百度一下"
print(item.url)
print(item.title)
```
