import asyncio
import typing

from maize.core.engine import Engine
from maize.exceptions.spider_exception import SpiderTypeException
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
        self.engine = self._create_engine()
        await self.engine.start_spider(self.spider)

    def _create_spider(self) -> "Spider":
        spider = self.spider_cls.create_instance(self)
        self._set_spider(spider)
        return spider

    def _create_engine(self):
        return Engine(self)

    def _set_spider(self, spider: "Spider"):
        merge_settings(spider=spider, settings=self.settings)


class CrawlerProcess:
    def __init__(self, settings: typing.Optional["SettingsManager"] = None):
        self.crawlers: typing.Final[set[Crawler]] = set()
        self._active: typing.Final[set] = set()
        self.settings: "SettingsManager" = settings if settings else get_settings()

    async def crawl(self, spider: typing.Type["Spider"]):
        crawler: Crawler = self._create_crawler(spider)
        self.crawlers.add(crawler)
        task = await self._crawl(crawler)
        self._active.add(task)

    @staticmethod
    async def _crawl(crawler: Crawler):
        return asyncio.create_task(crawler.crawl())

    async def start(self):
        await asyncio.gather(*self._active)

    def _create_crawler(self, spider_cls: typing.Type["Spider"]) -> Crawler:
        if isinstance(spider_cls, str):
            raise SpiderTypeException(
                f"{type(self)}.crawl args: String is not supported"
            )

        return Crawler(spider_cls, self.settings)
