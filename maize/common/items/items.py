"""
爬虫数据项基类。

定义 :class:`Item`，所有爬虫抓取的结构化数据均应继承此类。
"""

from maize.common.model.base_model import BaseModel


class Item(BaseModel):
    """
    爬虫数据项基类。

    继承自 :class:`~maize.common.model.base_model.BaseModel`（Pydantic），
    子类通过类型注解声明字段即可。

    :ivar __table_name__: 对应的数据库表名，默认为空字符串
    :ivar __retry_count__: 当前重试次数，默认为 0
    """

    __table_name__: str = ""
    __retry_count__: int = 0

    def retry(self):
        """
        将重试计数加一。
        """

        self.__retry_count__ += 1
