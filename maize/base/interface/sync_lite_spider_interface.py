"""
同步 Lite 爬虫接口。

与异步版 ``LiteSpiderInterface``（``maize.base.interface.lite_spider_interface``）对应，
方法均为同步（非 async）。``start_requests`` 返回普通 ``Generator``，
``parse`` 返回 ``Generator`` 或 None。
"""

from abc import ABC, abstractmethod
from collections.abc import Generator
from typing import TYPE_CHECKING, Union

from maize.base.interface._shared import _LiteSpiderConfig

if TYPE_CHECKING:
    from maize.common.http.request import Request
    from maize.common.http.response import Response
    from maize.common.items import Item


class SyncLiteSpiderInterface(_LiteSpiderConfig, ABC):
    """
    同步 Lite 爬虫接口。
    """

    @abstractmethod
    def start_requests(self) -> Generator["Request", None, None]:
        """
        生成起始请求。
        """

    @abstractmethod
    def parse(self, response: "Response") -> Generator[Union["Request", "Item"], None, None] | None:
        """
        解析响应。

        两种用法：
        1. 无需跟进链接：直接 return，与旧版行为一致
        2. 需要跟进链接或产出数据：yield Request（自动入队继续抓取）或 Item（自动收集）
        """
