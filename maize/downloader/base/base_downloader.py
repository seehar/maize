import asyncio
from abc import ABC, ABCMeta, abstractmethod
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any, Final, Union

from maize.common.http import Response
from maize.common.http.request import Request
from maize.common.model.download_response_model import DownloadResponse
from maize.utils.log_util import get_logger

if TYPE_CHECKING:
    from maize.core.crawler import Crawler


class ActiveRequestManager:
    def __init__(self):
        self._active: Final[set] = set()

    def add(self, request: Request):
        self._active.add(request)

    def remove(self, request: Request):
        self._active.remove(request)

    @asynccontextmanager
    async def __call__(self, request: Request):
        try:
            yield self.add(request)
        finally:
            self.remove(request)

    def __len__(self):
        return len(self._active)


class DownloaderMeta(ABCMeta):
    def __subclasscheck__(cls, subclass):
        required_method = ("fetch", "download", "create_instance", "close", "idle")
        return all(
            hasattr(subclass, method) and callable(getattr(subclass, method, None)) for method in required_method
        )


class BaseDownloader(ABC, metaclass=DownloaderMeta):
    def __init__(self, crawler: "Crawler"):
        self.crawler = crawler
        self._active = ActiveRequestManager()
        self._max_retry_count: int = self.crawler.settings.request.max_retry_count

        self.logger = get_logger(crawler.settings, self.__class__.__name__, crawler.settings.log_level)

    @classmethod
    def create_instance(cls, *args, **kwargs):
        return cls(*args, **kwargs)

    async def open(self):
        self.logger.info(
            f"{self.crawler.spider} <downloader class: {type(self).__name__}> "
            f"<concurrency: {self.crawler.settings.concurrency}>"
        )

    async def fetch(self, request: Request) -> Union[DownloadResponse, Request]:
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
        raise NotImplementedError

    def idle(self) -> bool:
        return len(self) == 0

    def __len__(self):
        return len(self._active)

    async def close(self):
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
