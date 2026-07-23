"""同步任务爬虫。

与异步版 ``TaskSpider`` 对应，``start_requests`` 返回普通 ``Generator``。
当无更多任务时，抛出 ``StopIteration`` 结束爬虫。
"""

import typing
from abc import abstractmethod
from collections.abc import Generator

from maize.common.http.request import Request
from maize.sync.classic.spider.sync_spider import SyncSpider


class SyncTaskSpider(SyncSpider):
    """同步任务爬虫。"""

    __spider_type__: str = "task_spider"

    @abstractmethod
    def start_requests(self) -> Generator[Request, typing.Any, None]:
        """
        生成任务请求。

        当无更多任务时，抛出 StopIteration 异常结束爬虫。
        """
        yield Request("")
