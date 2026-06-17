from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from maize.common.http.request import Request
    from maize.common.http.response import Response


class LiteSpiderInterface(ABC):
    """Lite 爬虫接口"""

    @property
    def concurrency(self) -> int:
        """最大并发数"""
        return 5

    @property
    def retry(self) -> int:
        """重试次数"""
        return 3

    @property
    def proxy(self) -> str | None:
        """代理地址"""
        return None

    @property
    def timeout(self) -> float:
        """请求超时时间（秒）"""
        return 30.0

    @abstractmethod
    async def start_requests(self) -> AsyncGenerator["Request", Any]:
        """生成起始请求"""

    @abstractmethod
    async def parse(self, response: "Response") -> None:
        """解析响应"""
