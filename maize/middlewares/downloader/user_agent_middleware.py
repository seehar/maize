"""
User-Agent 中间件

为请求轮换 User-Agent 请求头
"""

import random
from typing import TYPE_CHECKING

from maize.middlewares.base_middleware import DownloaderMiddleware

if TYPE_CHECKING:
    from maize.common.http.request import Request
    from maize.spider.spider import Spider


# 默认 User-Agent 列表
DEFAULT_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]


class UserAgentMiddleware(DownloaderMiddleware):
    """
    User-Agent 轮换中间件

    可以使用自定义的 User-Agent 列表或默认列表
    支持随机或顺序选择

    配置项:
        - user_agent_list: User-Agent 字符串列表（可选）
        - user_agent_mode: 'random' 或 'sequential'（默认: 'random'）
    """

    async def open(self):
        pass

    async def close(self):
        pass

    def __init__(self, settings=None, user_agent_list=None, mode="random"):
        """
        初始化 User-Agent 中间件

        :param settings: 爬虫配置
        :param user_agent_list: 自定义 User-Agent 列表
        :param mode: 选择模式（'random' 或 'sequential'）
        """
        super().__init__(settings)
        self.user_agent_list = user_agent_list or DEFAULT_USER_AGENTS
        self.mode = mode
        self.current_index = 0

    @classmethod
    def from_crawler(cls, crawler):
        """
        从 crawler 创建中间件实例

        :param crawler: Crawler 实例
        :return: UserAgentMiddleware 实例
        """
        settings = crawler.settings

        # 尝试从配置中获取 User-Agent 列表
        user_agent_list = getattr(settings, "user_agent_list", None)
        mode = getattr(settings, "user_agent_mode", "random")

        return cls(settings, user_agent_list=user_agent_list, mode=mode)

    async def process_request(self, request: "Request", spider: "Spider") -> "Request":
        """
        为请求设置 User-Agent 请求头

        :param request: 要处理的请求
        :param spider: 爬虫实例
        :return: 修改后的请求
        """
        # 如果已经设置了 User-Agent，则不覆盖
        if request.headers and "User-Agent" in request.headers:
            return request

        # 选择 User-Agent
        if self.mode == "sequential":
            user_agent = self.user_agent_list[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.user_agent_list)
        else:  # random
            user_agent = random.choice(self.user_agent_list)

        # 设置 User-Agent 请求头
        if not request.headers:
            request.headers = {}
        request.headers["User-Agent"] = user_agent

        return request
