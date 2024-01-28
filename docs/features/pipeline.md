# 数据管道 - Pipeline

Pipeline是数据入库时流经的管道，用户可自定义，以便对接其他数据库。
框架已内置基于 `aiomysql` 封装的 `mysql` 管道，其他管道继承 `BasePipeline` 类自行实现。

## 使用方式

> 注：`item` 会被聚合成多条一起流经 `pipeline`，方便批量入库。
> 框架内置的 `MysqlPipeline` 会自动入库，无需用户自行调用 `process_item` 方法。


### 自定义 `Pipeline`

```python
from maize import BasePipeline


class CustomPipeline(BasePipeline):
    
    async def open(self):
        """
        管道初始化时调用，需要初始化的异步方法请在此实现
        @return: 
        """
    
    async def close(self):
        """
        管道关闭时调用，需要关闭的异步方法请在此实现
        @return: 
        """
    
    async def process_item(self, items: list["Item"]):
        """
        处理数据，需要处理数据的方法请在此实现。
        为了提高效率，请使用异步方法。
        @param items: 
        @return: 
        """

    async def process_error_item(self, items: list["Item"]):
        """
        处理超过重试次数的数据
        @param items: 
        @return: 
        """
```


### 数据自动入库

需要在 `Item` 中增加 `__table_name__` 字段，此字段对应数据库表名，框架会自动将数据入库。

```python
from maize import Item, Field


class CustomItem(Item):
    __table_name__ = "custom_item"
    name = Field()  # 对应数据库表的字段
    # ...
```


### 注册 `Pipeline`

可以在 `settings.py` 中进行注册，也可以在 `spider.py` 中进行注册。
将编写好的 `pipeline` 配置进来，值为类的模块路径，需要指定到具体的类名

```python
# 数据管道，支持多个数据管道
# BasePipeline: 默认数据管道，不做任何处理
# MysqlPipeline: 集成 aiomysql 的数据管道，自动入库 mysql 数据库
ITEM_PIPELINES = ["maize.BasePipeline"]
```
