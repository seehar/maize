"""
任务型爬虫基类。

继承 Spider，用于需要从外部任务源生成请求的场景。
"""

import typing
from abc import abstractmethod

from maize.aio.classic.spider.spider import Spider
from maize.common.http import Request


class TaskSpider(Spider):
    """
    任务型爬虫，start_requests 用于生成任务请求。

    与 Spider 的区别在于语义上强调任务驱动，__spider_type__ 为 ``"task_spider"``。
    """

    __spider_type__: str = "task_spider"

    @abstractmethod
    async def start_requests(self) -> typing.AsyncGenerator[Request, typing.Any]:
        """
        生成任务请求
        :return:
        """
        yield Request("")
