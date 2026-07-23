"""同步管道基类。

与异步版 ``BasePipeline`` 对应，``open``/``close``/``process_item``/``process_error_item`` 均为同步。
"""

from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from maize.common.items import Item
    from maize.settings import SpiderSettings


class SyncBasePipeline(metaclass=ABCMeta):
    """同步数据管道基类。"""

    def __init__(self, settings: "SpiderSettings"):
        self.settings = settings

    @abstractmethod
    def open(self):
        """管道初始化时调用。"""

    @abstractmethod
    def close(self):
        """管道关闭时调用。"""

    @abstractmethod
    def process_item(self, items: list["Item"]) -> bool:
        """
        处理数据。

        :param items: 批量数据
        :return: 成功 True，否则 False
        """

    @abstractmethod
    def process_error_item(self, items: list["Item"]):
        """处理超过重试次数的数据。"""
