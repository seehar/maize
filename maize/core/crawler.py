import asyncio
import logging
import typing

from maize.core.engine import Engine
from maize.exceptions.spider_exception import SpiderTypeException
from maize.utils.log_util import get_logger, set_spider_settings
from maize.utils.project_util import get_settings

if typing.TYPE_CHECKING:
    from maize.settings import SpiderSettings
    from maize.spider.spider import Spider


class Crawler:
    def __init__(self, spider_cls: "Spider", settings: "SpiderSettings"):
        self.spider_cls = spider_cls
        self.spider: Spider | None = None
        self.engine: Engine | None = None
        self.settings: SpiderSettings = settings

    async def crawl(self):
        # 设置 settings 到上下文中，这样后续调用 get_logger() 时可以自动获取
        set_spider_settings(self.settings)

        self.spider = self._create_spider()
        await self.spider.open(self.settings)

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
            return get_settings(settings_path)
        except ModuleNotFoundError as e:
            logging.warning(f"{e} use default settings")
            return get_settings()
        except NameError as e:
            logging.warning(f"{e} use default settings")
            return get_settings()

    async def crawl(self, spider: typing.Union[typing.Type["Spider"], "Spider"]):
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

    def _create_crawler(self, spider_cls: "Spider") -> Crawler:
        if isinstance(spider_cls, str):
            raise SpiderTypeException(f"{type(self)}.crawl args: String is not supported")

        return Crawler(spider_cls, self.settings)
