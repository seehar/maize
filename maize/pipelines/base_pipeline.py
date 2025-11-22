from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from maize import Item
    from maize.settings import SpiderSettings


class BasePipeline(metaclass=ABCMeta):
    def __init__(self, settings: "SpiderSettings"):
        self.settings = settings

    @abstractmethod
    async def open(self):
        """
        管道初始化时调用，需要初始化的异步方法请在此实现
        @return:
        """

    @abstractmethod
    async def close(self):
        """
        管道关闭时调用，需要关闭的异步方法请在此实现
        @return:
        """

    @abstractmethod
    async def process_item(self, items: list["Item"]) -> bool:
        """
        处理数据，需要处理数据的方法请在此实现。
        为了提高效率，请使用异步方法。
        :param items:
        @return:
        """

    @abstractmethod
    async def process_error_item(self, items: list["Item"]):
        """
        处理超过重试次数的数据
        :param items:
        @return:
        """
