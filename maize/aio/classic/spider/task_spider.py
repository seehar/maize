import typing
from abc import abstractmethod

from maize.aio.classic.spider.spider import Spider
from maize.common.http import Request


class TaskSpider(Spider):
    __spider_type__: str = "task_spider"

    @abstractmethod
    async def start_requests(self) -> typing.AsyncGenerator[Request, typing.Any]:
        """
        生成任务请求
        :return:
        """
        yield Request("")
