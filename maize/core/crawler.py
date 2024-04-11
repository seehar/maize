import asyncio
import logging
import typing

from maize.core.engine import Engine
from maize.exceptions.spider_exception import SpiderTypeException
from maize.utils.log_util import get_logger
from maize.utils.project_util import get_settings
from maize.utils.project_util import merge_settings


if typing.TYPE_CHECKING:
    from maize.core.settings.settings_manager import SettingsManager
    from maize.core.spider.spider import Spider


class Crawler:
    def __init__(self, spider_cls: typing.Type["Spider"], settings: "SettingsManager"):
        self.spider_cls = spider_cls
        self.spider: typing.Optional["Spider"] = None
        self.engine: typing.Optional[Engine] = None
        self.settings: "SettingsManager" = settings.copy()

    async def crawl(self):
        self.spider = self._create_spider()
        await self.spider.open()

        self.engine = self._create_engine()
        await self.engine.start_spider(self.spider)

        await self.spider.close()

    def _create_spider(self) -> "Spider":
        """
        创建爬虫实例
        :return:
        """
        spider = self.spider_cls.create_instance(self)
        self._set_spider(spider)
        return spider

    def _create_engine(self):
        return Engine(self)

    def _set_spider(self, spider: "Spider"):
        """
        设置爬虫，合并配置
        :param spider: Spider类
        :return:
        """
        merge_settings(spider=spider, settings=self.settings)


class CrawlerProcess:
    """
    运行爬虫
    """

    def __init__(
        self,
        settings: typing.Optional["SettingsManager"] = None,
        settings_path: typing.Optional[str] = "settings.Settings",
    ):
        self.crawlers: typing.Final[set[Crawler]] = set()
        self._active: typing.Final[set] = set()
        self.settings: "SettingsManager" = (
            settings if settings else self.__get_settings(settings_path)
        )

        self.logger = get_logger(self.settings, self.__class__.__name__)

    @staticmethod
    def __get_settings(settings_path: typing.Optional[str]) -> "SettingsManager":
        """
        获取配置
        :param settings_path:
        :return:
        """
        try:
            return get_settings(settings_path)
        except ModuleNotFoundError as e:
            logging.warning(f"{e} use default settings")
            return get_settings()
        except NameError as e:
            logging.warning(f"{e} use default settings")
            return get_settings()

    async def crawl(self, spider: typing.Type["Spider"]):
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

    def _create_crawler(self, spider_cls: typing.Type["Spider"]) -> Crawler:
        if isinstance(spider_cls, str):
            raise SpiderTypeException(
                f"{type(self)}.crawl args: String is not supported"
            )

        return Crawler(spider_cls, self.settings)
