"""
同步 Spider 接口。

与异步版 `SpiderInterface` 对应，`start_requests` / `parse` / `open` / `close` 均为同步。
"""

from abc import ABC, abstractmethod
from collections.abc import Generator
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from maize.common.http.request import Request
    from maize.common.http.response import Response


class SyncSpiderInterface(ABC):
    """
    同步 Classic 爬虫抽象接口。

    所有同步 Classic Spider 的基类，声明 open / close / start_requests / parse 抽象方法。
    """

    def __init__(self):
        super().__init__()

    def __str__(self):
        return self.__class__.__name__

    @abstractmethod
    def open(self) -> None:
        """
        在 Spider 启动时执行初始化操作。
        """
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        """
        在 Spider 关闭时执行清理操作。
        """
        raise NotImplementedError

    @abstractmethod
    def start_requests(self) -> Generator["Request", Any, None]:
        """
        定义起始请求生成器，yield Request 实例。
        """
        raise NotImplementedError

    @abstractmethod
    def parse(self, response: "Response"):
        """
        自定义解析方法。
        """
        raise NotImplementedError
