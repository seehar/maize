"""
深度中间件

限制爬虫的爬取深度
"""

from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

from maize.middlewares.base_middleware import SpiderMiddleware

if TYPE_CHECKING:
    from maize.common.http.request import Request
    from maize.common.http.response import Response
    from maize.spider.spider import Spider


class DepthMiddleware(SpiderMiddleware):
    """
    深度限制中间件

    跟踪请求的深度并过滤超过最大深度的请求
    深度从 start_requests 的 0 开始，每个后续请求增加 1

    配置项:
        - max_depth: 最大爬取深度（默认: 0，不限制）
        - depth_priority_enabled: 是否根据深度调整优先级（默认: False）
    """

    async def close(self):
        pass

    async def open(self):
        pass

    def __init__(self, settings=None, max_depth=0, depth_priority_enabled=False):
        """
        初始化深度中间件

        :param settings: 爬虫配置
        :param max_depth: 最大爬取深度（0 = 不限制）
        :param depth_priority_enabled: 是否根据深度调整优先级
        """
        super().__init__(settings)
        self.max_depth = max_depth
        self.depth_priority_enabled = depth_priority_enabled

    @classmethod
    def from_crawler(cls, crawler):
        """
        从 crawler 创建中间件实例

        :param crawler: Crawler 实例
        :return: DepthMiddleware 实例
        """
        settings = crawler.settings

        max_depth = getattr(settings, "max_depth", 0)
        depth_priority_enabled = getattr(settings, "depth_priority_enabled", False)

        return cls(settings, max_depth=max_depth, depth_priority_enabled=depth_priority_enabled)

    def _get_depth(self, request: "Request") -> int:
        """
        从请求的 meta 中获取深度

        :param request: 请求实例
        :return: 深度值
        """
        if not request.meta:
            return 0
        return request.meta.get("depth", 0)

    def _set_depth(self, request: "Request", depth: int):
        """
        设置请求的深度到 meta 中

        :param request: 请求实例
        :param depth: 深度值
        """
        if not request.meta:
            request._meta = {}
        request._meta["depth"] = depth

    async def process_start_requests(self, start_requests: AsyncGenerator, spider: "Spider") -> AsyncGenerator:
        """
        为起始请求设置深度为 0

        :param start_requests: 起始请求生成器
        :param spider: 爬虫实例
        :return: 设置了深度为 0 的请求对象
        """
        async for request in start_requests:
            self._set_depth(request, 0)
            yield request

    async def process_spider_output(
        self, response: "Response", result: AsyncGenerator, spider: "Spider"
    ) -> AsyncGenerator:
        """
        处理爬虫输出并根据深度过滤

        :param response: 响应实例
        :param result: 爬虫输出生成器
        :param spider: 爬虫实例
        :return: 通过深度检查的 Request 或 Item 对象
        """
        # 获取当前响应的深度
        current_depth = self._get_depth(response.request)

        async for item in result:
            # 如果是 Request，检查并更新深度
            if item.__class__.__name__ == "Request":
                new_depth = current_depth + 1

                # 检查是否超过最大深度
                if 0 < self.max_depth < new_depth:
                    self.logger.debug(f"由于深度限制过滤请求 {item.url} ({new_depth} > {self.max_depth})")
                    continue

                # 为新请求设置深度
                self._set_depth(item, new_depth)

                # 如果启用，根据深度调整优先级
                if self.depth_priority_enabled:
                    # 深度越高 = 优先级越低（数字越大）
                    item.priority += new_depth

                self.logger.debug(f"请求 {item.url} 深度: {new_depth}")

            yield item
