# Item 数据项

`Item` 是 maize 对采集数据的封装，用于定义数据结构。在 `parse` 中 yield `Item` 后，数据会进入 Pipeline 链处理（Classic）或触发 `process_item` 钩子（Lite）。

## 定义 Item

自定义 `Item` 需要继承 `maize.Item`，字段使用 `Field` 定义：

```python
from maize import Field, Item


class BaiduItem(Item):
    __table_name__ = "baidu_hot_search"  # 数据库表名（使用 MySQL Pipeline 时必须设置）

    url: str = Field()
    title: str = Field(default="默认标题")
    rank: int = Field(default=0)
```

### 属性说明

| 属性 | 类型 | 默认值 | 说明 |
|:-----|:-----|:-------|:-----|
| `__table_name__` | `str` | `""` | 数据库表名。使用 MySQL Pipeline 自动入库时必须设置，否则跳过该 Item |
| `__retry_count__` | `int` | `0` | 入库失败重试计数，框架内部使用 |

### Field

`Field` 即 Pydantic 的 `Field`，支持所有 Pydantic 字段特性：

```python
from maize import Field, Item


class ArticleItem(Item):
    __table_name__ = "articles"

    title: str = Field(description="文章标题")
    content: str = Field(default="")
    view_count: int = Field(default=0, ge=0)  # 带验证：必须 >= 0
    tags: list[str] = Field(default_factory=list)  # 可变默认值用 default_factory
```

## 在 Spider 中使用

```python
from typing import Any, AsyncGenerator

from maize import Request, Response, Spider


class BaiduSpider(Spider):
    async def start_requests(self) -> AsyncGenerator[Request, Any]:
        yield Request(url="http://www.baidu.com")

    async def parse(self, response: Response):
        item = BaiduItem()
        item["url"] = response.url
        item["title"] = response.xpath("//title/text()").get()
        yield item
```

## 访问与赋值

Item 同时支持字典风格和属性风格的访问：

```python
item = BaiduItem()

# 字典风格
item["url"] = "https://www.baidu.com"
item["title"] = "百度一下"

# 属性风格
item.url = "https://www.baidu.com"
item.title = "百度一下"

# 读取也两种都行
assert item["url"] == item.url
```

## 序列化

### to_dict()

将 Item 转为字典，常用于自定义 Pipeline 中写入 CSV / JSON 等：

```python
item = BaiduItem(url="https://example.com", title="示例")
data = item.to_dict()
# {'url': 'https://example.com', 'title': '示例', 'rank': 0}
```

### model_dump()

Item 基于 Pydantic，支持 `model_dump()` / `model_dump_json()`：

```python
item = BaiduItem(url="https://example.com", title="示例")

item.model_dump()       # dict — 同 to_dict()
item.model_dump_json()  # str — JSON 字符串
```

## 与 Pipeline 配合

Classic 模式下，`parse` 中 yield 的 Item 会自动进入 Pipeline 链。Pipeline 的 `process_item` 接收 Item 列表，通过 `to_dict()` 和 `__table_name__` 实现自动入库：

```python
from typing import List
from maize import BasePipeline, Item


class MysqlPipeline(BasePipeline):
    async def process_item(self, items: List[Item]) -> bool:
        if not items:
            return True

        table_name = items[0].__table_name__
        columns = ', '.join(items[0].to_dict().keys())
        placeholders = ', '.join(['%s'] * len(items[0].to_dict()))
        sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"

        values = [tuple(item.to_dict().values()) for item in items]
        # ... 执行 SQL ...
        return True
```

Lite 模式下，重写 `process_item` 钩子处理数据：

```python
from maize.aio.lite import LiteSpider, Request, Response
from maize import Item


class MySpider(LiteSpider):
    async def process_item(self, item: Item) -> None:
        """重写以实现数据落盘"""
        self.logger.info(f"采集到数据: {item.to_dict()}")

    async def start_requests(self):
        yield Request(url="https://example.com")

    async def parse(self, response: Response):
        yield BaiduItem(url=response.url, title=response.xpath("//title/text()").get())
```

## 下一步

- [Pipeline 管道](pipeline.md) - 数据管道使用
- [Spider 进阶](spider.md) - 在爬虫中使用 Item
- [Response 详解](response.md) - 从响应中提取数据
