"""
下载器抽象基类。

定义所有下载器（aiohttp / httpx / requests 等）的公共生命周期与活跃请求跟踪机制。
"""

import asyncio
from abc import ABC, ABCMeta, abstractmethod
from contextlib import AbstractAsyncContextManager
from types import TracebackType
from typing import TYPE_CHECKING, Any, Final, Union

from maize.common.http import Response
from maize.common.http.request import Request
from maize.common.model.download_response_model import DownloadResponse
from maize.utils.log_util import get_logger

if TYPE_CHECKING:
    from maize.aio.classic.crawler.crawler import Crawler


class ActiveRequestContextManager(AbstractAsyncContextManager):
    """
    活跃请求异步上下文管理器。

    进入时将请求注册到 ActiveRequestManager，退出时自动移除，
    用于跟踪下载器当前正在处理的请求数量。

    :param manager: 所属的 ActiveRequestManager 实例
    :param request: 要跟踪的 Request 实例
    """

    def __init__(self, manager: "ActiveRequestManager", request: Request):
        """
        初始化上下文管理器。

        :param manager: 所属的 ActiveRequestManager 实例
        :param request: 要跟踪的 Request 实例
        """
        self._manager = manager
        self._request = request

    async def __aenter__(self) -> None:
        self._manager.add(self._request)

    async def __aexit__(
        self, exc_type: type | None, exc_val: BaseException | None, exc_tb: TracebackType | None
    ) -> bool | None:
        self._manager.remove(self._request)
        return None


class ActiveRequestManager:
    """
    活跃请求管理器。

    维护一个 Request 集合，记录当前正在下载中的请求。
    通过 __call__ 返回 ActiveRequestContextManager 以支持 async with 用法。
    """

    def __init__(self):
        """
        初始化活跃请求集合。
        """
        self._active: Final[set] = set()

    def add(self, request: Request):
        """
        将请求标记为活跃状态。

        :param request: 开始下载的 Request 实例
        """
        self._active.add(request)

    def remove(self, request: Request):
        """
        将请求从活跃集合中移除。

        :param request: 已完成下载的 Request 实例
        :raises KeyError: 请求不在活跃集合中时抛出
        """
        self._active.remove(request)

    def __call__(self, request: Request) -> ActiveRequestContextManager:
        return ActiveRequestContextManager(self, request)

    def __len__(self):
        return len(self._active)


class DownloaderMeta(ABCMeta):
    """
    下载器元类。

    通过 __subclasscheck__ 实现结构化子类型检查：
    只要类拥有 fetch / download / create_instance / close / idle 方法即视为下载器。
    """

    def __subclasscheck__(cls, subclass):
        required_method = ("fetch", "download", "create_instance", "close", "idle")
        return all(
            hasattr(subclass, method) and callable(getattr(subclass, method, None)) for method in required_method
        )


class BaseDownloader(ABC, metaclass=DownloaderMeta):
    """
    下载器抽象基类。

    所有具体下载器（HTTPXDownloader、AiohttpDownloader 等）的父类，
    提供活跃请求跟踪、重试逻辑、随机等待等公共能力。

    :param crawler: 关联的 Crawler 实例，提供 settings 和 spider 引用
    """

    def __init__(self, crawler: "Crawler"):
        """
        初始化下载器。

        :param crawler: 关联的 Crawler 实例，提供 settings 和 spider 引用
        """
        self.crawler = crawler
        self._active = ActiveRequestManager()
        self._max_retry_count: int = self.crawler.settings.request.max_retry_count

        self.logger = get_logger(crawler.settings, self.__class__.__name__, crawler.settings.log_level)

    @classmethod
    def create_instance(cls, *args, **kwargs):
        """
        创建下载器实例（类方法工厂）。

        :param args: 传递给构造函数的位置参数
        :param kwargs: 传递给构造函数的关键字参数
        :return: 下载器实例
        """
        return cls(*args, **kwargs)

    async def open(self):
        """
        下载器启动钩子，记录启动日志。

        子类可重写以执行连接池初始化等操作。
        """
        self.logger.info(
            f"{self.crawler.spider} <downloader class: {type(self).__name__}> "
            f"<concurrency: {self.crawler.settings.concurrency}>"
        )

    async def fetch(self, request: Request) -> Union[DownloadResponse, Request]:
        """
        执行下载并自动跟踪活跃请求。

        通过 ActiveRequestContextManager 确保请求在下载期间被计入活跃集合，
        下载完成（无论成功或异常）后自动移除。

        :param request: 待下载的 Request 实例
        :return: DownloadResponse（成功）或 Request（需重试时原样返回）
        """
        async with self._active(request):
            return await self.download(request)

    @abstractmethod
    async def download(self, request: Request) -> Union[DownloadResponse, Request]:
        """
        下载

        :param request: 请求实例
        :return: 返回 DownloadResponse 实例或 Request 实例
        """
        raise NotImplementedError

    async def _download_retry(self, request: Request, exception: Exception) -> Request | None:
        """
        下载重试
        :param request: 请求
        :param exception: 上次请求失败的异常
        :return:
        """
        if request.current_retry_count < self._max_retry_count:
            self.logger.info(
                f"Retrying request({request.current_retry_count + 1}/{self._max_retry_count}): {request.url}. "
                f"Error during request {exception}. "
            )
            request.retry()
            return request

        self.logger.error(f"Max retry count reached ({self._max_retry_count}). Skipping request: {request.url}")
        await self.process_error_request(request)
        return None

    @staticmethod
    @abstractmethod
    def structure_response(request: Request, response: Any, body: bytes) -> Response:
        """
        将原始 HTTP 响应封装为框架 Response 对象。

        :param request: 原始 Request 实例
        :param response: 底层 HTTP 库的原始响应对象
        :param body: 响应体字节内容
        :return: 封装后的 Response 实例
        """
        raise NotImplementedError

    def idle(self) -> bool:
        """
        判断下载器是否空闲（无活跃请求）。

        :return: 活跃请求数为 0 时返回 True
        """
        return len(self) == 0

    def __len__(self):
        return len(self._active)

    async def close(self):
        """
        下载器关闭钩子，记录关闭日志。

        子类可重写以释放连接池等资源。
        """
        self.logger.info(f"{self.crawler.spider} <downloader class: {type(self).__name__}> closed")

    async def process_error_request(self, request: Request):
        """
        处理超过最大重试次数的请求
        :param request:
        :return:
        """

    async def random_wait(self):
        """
        随机等待

        :return:
        """
        await asyncio.sleep(*self.crawler.settings.request.random_wait_time)
