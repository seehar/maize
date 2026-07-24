"""
异步 Classic 爬虫接口。

定义 Spider 需实现的抽象契约：open / close 生命周期钩子、
start_requests 起始请求生成器、parse 响应解析方法。

同步版对应接口：``maize.base.interface.sync_spider_interface.SyncSpiderInterface``
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from maize.common.http.request import Request
    from maize.common.http.response import Response


class SpiderInterface(ABC):
    """
    异步 Classic 爬虫抽象接口。

    所有异步 Classic Spider 的基类，声明 open / close / start_requests / parse 抽象方法。
    """

    def __init__(self):
        super().__init__()

    def __str__(self):
        return self.__class__.__name__

    @abstractmethod
    async def open(self) -> None:
        """
        在 Spider 启动时执行一些初始化操作

        :return:
        """
        raise NotImplementedError

    @abstractmethod
    async def close(self) -> None:
        """
        在 Spider 关闭时执行一些清理操作

        :return:
        """
        raise NotImplementedError

    @abstractmethod
    def start_requests(self) -> AsyncGenerator["Request", Any]:
        """
        定义起始请求生成器

        :return: 异步生成器，产生 Request 实例
        """
        raise NotImplementedError

    @abstractmethod
    def parse(self, response: "Response"):
        """
        自定义解析方法

        :param response: 封装后的响应实例
        :return:
        """
        raise NotImplementedError
