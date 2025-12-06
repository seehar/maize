"""
Maize 框架的基础中间件类

本模块为所有中间件类型提供基础：
- BaseMiddleware: 所有中间件的公共基类
- DownloaderMiddleware: 处理请求和响应
- SpiderMiddleware: 处理爬虫输入/输出
- PipelineMiddleware: 处理 Pipeline 前后的 Item
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Any

from maize.utils.log_util import get_logger

if TYPE_CHECKING:
    from maize.common.http.request import Request
    from maize.common.http.response import Response
    from maize.common.items import Item
    from maize.spider.spider import Spider


class BaseMiddleware(ABC):
    """
    所有中间件类型的基类

    提供所有中间件共享的公共生命周期方法
    """

    def __init__(self, settings: Any = None):
        """
        初始化中间件

        :param settings: 爬虫配置对象
        """
        self.settings = settings
        self.logger = get_logger(settings)

    @classmethod
    def from_crawler(cls, crawler: Any) -> "BaseMiddleware":
        """
        从 crawler 创建中间件实例

        这是实例化中间件的推荐方式，因为它提供了对 crawler 和 settings 的访问

        :param crawler: Crawler 实例
        :return: 中间件实例
        """
        return cls(crawler.settings)

    @abstractmethod
    async def open(self):
        """
        爬虫打开时调用

        用于初始化资源，如数据库连接、文件等
        """
        pass

    @abstractmethod
    async def close(self):
        """
        爬虫关闭时调用

        用于清理资源，如数据库连接、文件等
        """
        pass


class DownloaderMiddleware(BaseMiddleware):
    """
    下载器中间件基类

    下载器中间件在请求发送到下载器之前和响应接收之后处理它们
    """

    async def open(self):
        pass

    async def close(self):
        pass

    async def process_request(self, request: "Request", spider: "Spider") -> "Request | Response | None":
        """
        在请求发送到下载器之前处理请求

        :param request: 要处理的请求
        :param spider: 生成请求的爬虫
        :return:
            - Request: 修改后的请求，继续处理
            - Response: 响应对象，跳过下载
            - None: 丢弃请求（不再继续处理）
        """
        return request

    async def process_response(
        self, request: "Request", response: "Response", spider: "Spider"
    ) -> "Response | Request | None":
        """
        在从下载器接收响应后处理响应

        :param request: 生成响应的请求
        :param response: 要处理的响应
        :param spider: 生成请求的爬虫
        :return:
            - Response: 修改后的响应，继续处理
            - Request: 新请求，重试（将返回调度器）
            - None: 丢弃响应（不再继续处理）
        """
        return response

    async def process_exception(
        self, request: "Request", exception: Exception, spider: "Spider"
    ) -> "Request | Response | None":
        """
        处理下载过程中引发的异常

        :param request: 导致异常的请求
        :param exception: 引发的异常
        :param spider: 生成请求的爬虫
        :return:
            - Request: 新请求，重试
            - Response: 响应对象，替代使用
            - None: 忽略异常并继续
        """
        return None


class SpiderMiddleware(BaseMiddleware):
    """
    爬虫中间件基类

    爬虫中间件处理爬虫回调的输入和输出
    """

    async def open(self):
        pass

    async def close(self):
        pass

    async def process_spider_input(self, response: "Response", spider: "Spider") -> None:
        """
        在响应传递给爬虫回调之前处理响应

        :param response: 要处理的响应
        :param spider: 爬虫实例
        :raises Exception: 触发 process_spider_exception
        """
        pass

    async def process_spider_output(
        self, response: "Response", result: AsyncGenerator, spider: "Spider"
    ) -> AsyncGenerator:
        """
        处理爬虫回调返回的结果

        :param response: 生成结果的响应
        :param result: Request 和/或 Item 对象的异步生成器
        :param spider: 爬虫实例
        :return: Request 或 Item 对象
        """
        async for item in result:
            yield item

    async def process_spider_exception(
        self, response: "Response", exception: Exception, spider: "Spider"
    ) -> AsyncGenerator | None:
        """
        处理爬虫回调引发的异常

        :param response: 发生异常时正在处理的响应
        :param exception: 引发的异常
        :param spider: 爬虫实例
        :return: Request/Item 对象的异步生成器，或 None 继续传播异常
        """
        return None

    async def process_start_requests(self, start_requests: AsyncGenerator, spider: "Spider") -> AsyncGenerator:
        """
        处理 start_requests 生成器

        :param start_requests: 起始请求生成器
        :param spider: 爬虫实例
        :return: Request 对象
        """
        async for request in start_requests:
            yield request


class PipelineMiddleware(BaseMiddleware):
    """
    管道中间件基类

    管道中间件在 Item 进入和离开 Pipeline 时处理它们
    """

    async def open(self):
        pass

    async def close(self):
        pass

    async def process_item_before(self, item: "Item", spider: "Spider") -> "Item | None":
        """
        在 Item 进入 Pipeline 之前处理 Item

        :param item: 要处理的 Item
        :param spider: 生成 Item 的爬虫
        :return:
            - Item: 修改后的 Item，继续处理
            - None: 丢弃 Item（不会被 Pipeline 处理）
        """
        return item

    async def process_item_after(self, item: "Item", spider: "Spider") -> "Item | None":
        """
        在 Item 离开 Pipeline 之后处理 Item

        :param item: 已处理的 Item
        :param spider: 生成 Item 的爬虫
        :return:
            - Item: 修改后的 Item
            - None: 丢弃 Item
        """
        return item
