"""
Spider 接口共享基类。

提取 async/sync 接口对中完全相同的部分，避免逐行复制导致的漂移：

- ``_SpiderContract``: ``__init__`` / ``__str__``，Classic Spider 和 Lite Spider 共用。
- ``_StandardSpiderMixin``: ``create_instance`` / ``idle``，Standard 接口对共用。
- ``_LiteSpiderConfig``: ``concurrency`` / ``retry`` / ``proxy`` / ``timeout`` 默认配置属性，
  Lite 接口对共用。

异步/同步差异（``async def`` vs ``def``、``AsyncGenerator`` vs ``Generator``）
留在各自的接口类中声明，不在此共享。
"""

from abc import ABC
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class _SpiderContract(ABC):  # noqa: B024
    """
    Spider 契约共享部分。

    提供 ``__init__`` 和 ``__str__``，被异步和同步 Spider 接口共同继承。
    """

    def __init__(self):
        super().__init__()

    def __str__(self):
        return self.__class__.__name__


class _StandardSpiderMixin:
    """
    Standard Spider 共享方法。

    ``create_instance`` 和 ``idle`` 在异步/同步 StandardSpiderInterface 中逻辑完全一致，
    仅 crawler 类型标注不同（运行时不影响）。提取到此处避免复制粘贴漂移。
    """

    __spider_type__: str

    @classmethod
    def create_instance(cls, crawler):
        """
        创建 Spider 实例并绑定 Crawler。

        :param crawler: 关联的 Crawler 实例
        :return: 绑定了 crawler 的 Spider 实例
        """
        instance = cls()
        instance.crawler = crawler
        return instance

    def idle(self) -> bool:
        """
        判断爬虫是否空闲。

        :return: 如果爬虫没有待处理的请求或任务，返回 True，否则返回 False
        """
        return True


class _LiteSpiderConfig:
    """
    Lite Spider 共享配置属性。

    ``concurrency`` / ``retry`` / ``proxy`` / ``timeout`` 的默认值在异步和同步
    LiteSpiderInterface 中完全一致，提取到此处避免修改默认值时只改一侧。
    """

    @property
    def concurrency(self) -> int:
        """
        最大并发数。
        """
        return 5

    @property
    def retry(self) -> int:
        """
        重试次数。
        """
        return 3

    @property
    def proxy(self) -> str | None:
        """
        代理地址。
        """
        return None

    @property
    def timeout(self) -> float:
        """
        请求超时时间（秒）。
        """
        return 30.0
