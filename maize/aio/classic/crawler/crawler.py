"""
Classic 异步爬虫运行器。

包含 Crawler（单个爬虫实例的生命周期管理）和 CrawlerProcess（多爬虫进程级调度入口）。
"""

import asyncio
import logging
import typing

from maize.core.engine.aio_engine import AioEngine
from maize.exceptions.spider_exception import SpiderTypeException
from maize.utils.log_util import get_logger, set_spider_settings
from maize.utils.project_util import get_settings

if typing.TYPE_CHECKING:
    from maize.base.interface.standard_spider_interface import StandardSpiderInterface
    from maize.settings import SpiderSettings


class Crawler:
    """
    单个爬虫实例的运行容器。

    负责创建 Spider 实例、初始化 AioEngine 并驱动完整的爬取生命周期。

    :param spider_cls: 爬虫类（StandardSpiderInterface 的实现类）
    :param settings: 爬虫全局配置
    """

    def __init__(self, spider_cls: "StandardSpiderInterface", settings: "SpiderSettings"):
        self.spider_cls = spider_cls
        self.spider: StandardSpiderInterface | None = None
        self.engine: AioEngine | None = None
        self.settings: SpiderSettings = settings

    async def crawl(self):
        """
        执行爬虫主流程。

        依次完成：设置上下文 → 创建 Spider → open → 启动引擎 → close。
        """
        # 设置 settings 到上下文中，这样后续调用 get_logger() 时可以自动获取
        set_spider_settings(self.settings)

        self.spider = self._create_spider()
        await self.spider.open()

        self.engine = self._create_engine()
        await self.engine.start_spider(self.spider)

        await self.spider.close()

    def _create_spider(self) -> "StandardSpiderInterface":
        """
        创建爬虫实例
        :return:
        """
        spider = self.spider_cls.create_instance(self)
        self._set_spider(spider)
        return spider

    def _create_engine(self):
        return AioEngine(self)

    def _set_spider(self, spider: "StandardSpiderInterface"):
        """
        设置爬虫，合并配置
        :param spider: Spider类
        :return:
        """
        try:
            custom_settings = spider.custom_settings
        except AttributeError:
            custom_settings = None

        if custom_settings:
            # 支持 SpiderSettings 类型和 dict 类型
            if hasattr(custom_settings, "model_dump"):
                self.settings.merge_settings(custom_settings)
            else:
                self.settings.merge_settings_from_dict(custom_settings)

    def idle(self) -> bool:
        """
        判断爬虫是否空闲（无待处理请求且未暂停）。

        :return: 空闲返回 True，否则 False
        """
        return self.spider.idle()


class CrawlerProcess:
    """
    运行爬虫
    """

    def __init__(
        self,
        settings: typing.Optional["SpiderSettings"] = None,
        settings_path: str | None = "settings.Settings",
    ):
        """
        初始化爬虫进程。

        :param settings: SpiderSettings 实例，为 None 时从 settings_path 加载
        :param settings_path: 配置模块路径，默认 ``"settings.Settings"``，加载失败时回退到默认配置
        """
        self.crawlers: typing.Final[set[Crawler]] = set()
        self._active: typing.Final[set] = set()
        self.settings: SpiderSettings = settings if settings else self.__get_settings(settings_path)

        self.logger = get_logger(self.settings, self.__class__.__name__)

    @staticmethod
    def __get_settings(settings_path: str | None) -> "SpiderSettings":
        """
        获取配置
        :param settings_path:
        :return:
        """
        try:
            return get_settings(settings_path)  # type: ignore[arg-type]
        except (ModuleNotFoundError, NameError, TypeError) as e:
            logging.warning(f"{e} use default settings")
            return get_settings()

    async def crawl(self, spider: typing.Union[typing.Type["StandardSpiderInterface"], "StandardSpiderInterface"]):
        """
        装配爬虫
        :param spider: Spider类
        :return:
        """
        crawler: Crawler = self._create_crawler(spider)
        self.crawlers.add(crawler)
        task = await self._crawl(crawler)
        self._active.add(task)

    @staticmethod
    async def _crawl(crawler: Crawler):
        return asyncio.create_task(crawler.crawl())

    async def start(self):
        """
        开始运行所有爬虫
        :return:
        """
        await asyncio.gather(*self._active)

    def _create_crawler(self, spider_cls: "StandardSpiderInterface") -> Crawler:
        if isinstance(spider_cls, str):
            raise SpiderTypeException(f"{type(self)}.crawl args: String is not supported")

        return Crawler(spider_cls, self.settings)
