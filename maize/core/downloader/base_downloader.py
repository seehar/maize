import typing
from abc import ABCMeta
from abc import abstractmethod
from contextlib import asynccontextmanager

from maize.core.http.request import Request
from maize.core.http.response import Response
from maize.utils.log_util import get_logger


if typing.TYPE_CHECKING:
    from maize.core.crawler import Crawler


class ActiveRequestManager:
    def __init__(self):
        self._active: typing.Final[set] = set()

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
    def __subclasscheck__(self, subclass):
        required_method = ("fetch", "download", "create_instance", "close", "idle")
        return all(
            hasattr(subclass, method) and callable(getattr(subclass, method, None))
            for method in required_method
        )


class BaseDownloader(metaclass=DownloaderMeta):
    def __init__(self, crawler: "Crawler"):
        self.crawler = crawler
        self._active = ActiveRequestManager()
        self._max_retry_count: int = self.crawler.settings.getint("MAX_RETRY_COUNT")

        self.logger = get_logger(
            crawler, self.__class__.__name__, crawler.settings.get("LOG_LEVEL")
        )

    @classmethod
    def create_instance(cls, *args, **kwargs):
        return cls(*args, **kwargs)

    def open(self):
        self.logger.info(
            f"{self.crawler.spider} <downloader class: {type(self).__name__}> "
            f"<concurrency: {self.crawler.settings.getint('CONCURRENCY')}>"
        )

    async def fetch(self, request: Request) -> typing.Optional[Response | Request]:
        async with self._active(request):
            return await self.download(request)

    @abstractmethod
    async def download(self, request: Request) -> typing.Optional[Response]:
        raise NotImplementedError

    async def _download_retry(
        self, request: Request, exception: Exception
    ) -> typing.Optional[Request]:
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

        self.logger.error(
            f"Max retry count reached ({self._max_retry_count}). Skipping request: {request.url}"
        )
        return None

    @staticmethod
    @abstractmethod
    def structure_response(
        request: Request, response: typing.Any, body: bytes
    ) -> Response:
        raise NotImplementedError

    def idle(self) -> bool:
        return len(self) == 0

    def __len__(self):
        return len(self._active)

    async def close(self):
        self.logger.info(
            f"{self.crawler.spider} <downloader class: {type(self).__name__}> closed"
        )
