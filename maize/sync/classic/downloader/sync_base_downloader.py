"""同步下载器基类。

与异步版 ``BaseDownloader`` 对应，``download``/``open``/``close``/``fetch`` 均为同步。
不使用 asyncio，并发由 ``SyncEngine`` 的线程池管理。
"""

import random
import time
import typing
from abc import ABC, ABCMeta, abstractmethod
from typing import TYPE_CHECKING, Union

from maize.common.http import Response
from maize.common.http.request import Request
from maize.common.model.download_response_model import DownloadResponse
from maize.utils.log_util import get_logger

if TYPE_CHECKING:
    from maize.sync.classic.crawler.sync_crawler import SyncCrawler


class SyncDownloaderMeta(ABCMeta):
    """
    同步下载器元类，校验子类是否实现了 download 和 structure_response。
    """

    def __subclasscheck__(cls, subclass):
        return (
            issubclass(subclass, SyncBaseDownloader)
            and hasattr(subclass, "download")
            and hasattr(subclass, "structure_response")
        )


class SyncBaseDownloader(ABC, metaclass=SyncDownloaderMeta):
    """同步下载器基类。"""

    def __init__(self, crawler: "SyncCrawler"):
        self.crawler = crawler
        self.logger = get_logger(crawler.settings, self.__class__.__name__, crawler.settings.log_level)

    def open(self):
        """
        打开下载器，打印下载器类和并发数信息。
        """
        self.logger.info(
            f"{self.crawler.spider} <downloader class: {type(self).__name__}> "
            f"<concurrency: {self.crawler.settings.concurrency}>"
        )

    def fetch(self, request: Request) -> Union[DownloadResponse, Request]:
        """执行下载（含随机等待）。"""
        self.random_wait()
        return self.download(request)

    @abstractmethod
    def download(self, request: Request) -> Union[DownloadResponse, Request]:
        """
        执行下载（子类必须实现）。

        :param request: 请求对象
        :return: ``DownloadResponse`` 或重试用的 ``Request``
        """
        raise NotImplementedError

    def _download_retry(self, request: Request, exception: Exception) -> Request | None:
        """
        下载重试。

        :param request: 请求
        :param exception: 异常
        :return: 需要重试时返回 Request，否则 None
        """
        retry_count = request.current_retry_count
        max_retry_count = self.crawler.settings.request.max_retry_count
        if retry_count < max_retry_count:
            request.retry()
            self.logger.warning(f"retry {request.url} for {exception}, retry times: {request.current_retry_count}")
            return request
        return None

    def close(self):
        """
        关闭下载器，打印关闭日志。
        """
        self.logger.info(f"{self.crawler.spider} <downloader class: {type(self).__name__}> closed")

    def process_error_request(self, request: Request):
        """处理超过最大重试次数的请求（子类可重写）。"""

    def random_wait(self):
        """随机等待，礼貌抓取。"""
        min_wait, max_wait = self.crawler.settings.request.random_wait_time
        if max_wait > min_wait:
            wait = random.uniform(min_wait, max_wait)
            time.sleep(wait)
        elif min_wait > 0:
            time.sleep(min_wait)

    @staticmethod
    @abstractmethod
    def structure_response(request: Request, response: typing.Any, body: bytes) -> Response:
        """将底层响应封装为 ``maize.Response``。"""
        raise NotImplementedError

    def idle(self) -> bool:
        """下载器是否空闲（同步版默认无 in-flight 跟踪，返回 True）。"""
        return True
