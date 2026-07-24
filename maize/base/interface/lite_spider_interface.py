"""
异步 Lite 爬虫接口。

定义 LiteSpider 需实现的抽象契约，包括并发、重试、代理等配置属性
以及 start_requests / parse 抽象方法。
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Any, Union

if TYPE_CHECKING:
    from maize.common.http.request import Request
    from maize.common.http.response import Response
    from maize.common.items import Item


class LiteSpiderInterface(ABC):
    """
    Lite 爬虫接口。
    """

    @property
    def concurrency(self) -> int:
        """
        最大并发数。
        """
        return 5

    @property
    def retry(self) -> int:
        """
        重试次数。
        """
        return 3

    @property
    def proxy(self) -> str | None:
        """
        代理地址。
        """
        return None

    @property
    def timeout(self) -> float:
        """
        请求超时时间（秒）。
        """
        return 30.0

    @abstractmethod
    async def start_requests(self) -> AsyncGenerator["Request", Any]:
        """
        生成起始请求。
        """

    @abstractmethod
    async def parse(self, response: "Response") -> AsyncGenerator[Union["Request", "Item"], Any] | None:
        """
        解析响应。

        两种用法：
        1. 无需跟进链接：直接 return，与旧版行为一致
        2. 需要跟进链接或产出数据：yield Request（自动入队继续抓取）或 Item（自动收集）
        """
