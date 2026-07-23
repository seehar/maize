"""同步中间件基类。

与异步版 ``BaseMiddleware`` 对应，所有方法均为同步（非 async）。
``from_crawler`` 复用同一 ``SyncCrawler``，``open``/``close``/``process_*`` 均为同步。
"""

from abc import ABC, abstractmethod
from collections.abc import Generator
from typing import TYPE_CHECKING

from maize.utils.log_util import get_logger

if TYPE_CHECKING:
    from maize.common.http.request import Request
    from maize.common.http.response import Response
    from maize.common.items import Item
    from maize.settings import SpiderSettings
    from maize.sync.classic.crawler.sync_crawler import SyncCrawler
    from maize.sync.classic.spider.sync_spider import SyncSpider


class SyncBaseMiddleware(ABC):
    """同步中间件基类。"""

    def __init__(self, settings: "SpiderSettings" = None):
        """
        :param settings: SpiderSettings 实例
        """
        self.settings = settings
        self.logger = get_logger(settings)

    @classmethod
    def from_crawler(cls, crawler: "SyncCrawler") -> "SyncBaseMiddleware":
        """从 Crawler 实例创建中间件。"""
        return cls(crawler.settings)

    @abstractmethod
    def open(self):
        """初始化中间件。"""
        pass

    @abstractmethod
    def close(self):
        """关闭中间件。"""
        pass


class SyncDownloaderMiddleware(SyncBaseMiddleware):
    """同步下载器中间件基类。"""

    def open(self):
        pass

    def close(self):
        pass

    def process_request(self, request: "Request", spider: "SyncSpider") -> "Request | Response | None":
        """
        请求发送前处理。

        - 返回 Request：用新请求继续传递给下一个中间件
        - 返回 Response：短路，跳过下载
        - 返回 None：丢弃请求
        - 不返回（隐式 None）：继续传递原请求
        """
        return request

    def process_response(
        self, request: "Request", response: "Response", spider: "SyncSpider"
    ) -> "Response | Request | None":
        """
        响应返回后处理。

        - 返回 Response：继续传递给下一个中间件
        - 返回 Request：重试
        - 返回 None：丢弃响应
        """
        return response

    def process_exception(
        self, request: "Request", exception: Exception, spider: "SyncSpider"
    ) -> "Request | Response | None":
        """
        下载异常处理。

        - 返回 Request：重试
        - 返回 Response：用该响应继续
        - 返回 None：继续传播异常
        """
        return None


class SyncSpiderMiddleware(SyncBaseMiddleware):
    """同步爬虫中间件基类。"""

    def open(self):
        pass

    def close(self):
        pass

    def process_spider_input(self, response: "Response", spider: "SyncSpider") -> bool:
        """响应传递给回调前处理。返回 False 中止。"""
        return True

    def process_spider_output(self, response: "Response", result: Generator, spider: "SyncSpider") -> Generator:
        """处理爬虫回调返回的结果。"""
        yield from result

    def process_spider_exception(
        self, response: "Response", exception: Exception, spider: "SyncSpider"
    ) -> Generator | None:
        """处理爬虫回调中的异常。返回生成器或 None。"""
        return None

    def process_start_requests(self, start_requests: Generator, spider: "SyncSpider") -> Generator:
        """处理起始请求生成器。"""
        yield from start_requests


class SyncPipelineMiddleware(SyncBaseMiddleware):
    """同步管道中间件基类。"""

    def open(self):
        pass

    def close(self):
        pass

    def process_item_before(self, item: "Item", spider: "SyncSpider") -> "Item | None":
        """Item 进入管道前处理。返回 None 丢弃。"""
        return item

    def process_item_after(self, item: "Item", spider: "SyncSpider") -> "Item | None":
        """Item 离开管道后处理。返回 None 丢弃。"""
        return item
