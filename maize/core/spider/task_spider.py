import typing
from abc import abstractmethod

from maize import Request
from maize import Spider


class TaskSpider(Spider):
    __spider_type__: str = "task_spider"

    @abstractmethod
    async def task_requests(self) -> typing.AsyncGenerator[Request, typing.Any]:
        """
        生成任务请求
        :return:
        """
        yield Request("")
