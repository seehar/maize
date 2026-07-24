"""
管道抽象基类。

定义 Pipeline 的生命周期接口（open/close）和数据处理接口（process_item/process_error_item），
所有自定义管道必须继承 BasePipeline 并实现全部抽象方法。
"""

from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from maize import Item
    from maize.settings import SpiderSettings


class BasePipeline(metaclass=ABCMeta):
    """
    管道抽象基类，定义数据持久化处理的标准接口。

    :param settings: 爬虫配置对象，包含数据库连接等管道所需参数
    """

    def __init__(self, settings: "SpiderSettings"):
        self.settings = settings

    @abstractmethod
    async def open(self):
        """
        管道初始化时调用，需要初始化的异步资源（如数据库连接）请在此实现。
        """

    @abstractmethod
    async def close(self):
        """
        管道关闭时调用，需要释放的异步资源请在此实现。
        """

    @abstractmethod
    async def process_item(self, items: list["Item"]) -> bool:
        """
        批量处理数据项，子类在此实现具体的持久化逻辑。

        :param items: 待处理的 Item 列表
        :return: 处理成功返回 True，失败返回 False
        """

    @abstractmethod
    async def process_error_item(self, items: list["Item"]):
        """
        处理超过重试次数仍失败的数据项。

        :param items: 超过最大重试次数的 Item 列表
        """
