"""同步 Classic 爬虫 Crawler 和 CrawlerProcess。

与异步版对应，``Crawler.crawl()`` 和 ``CrawlerProcess.start()`` 均为同步。
不使用 asyncio，引擎在线程池中执行并发请求。
"""

import logging
import typing

from maize.exceptions.spider_exception import SpiderTypeException
from maize.sync.classic.engine.sync_engine import SyncEngine
from maize.utils.log_util import get_logger, set_spider_settings
from maize.utils.project_util import get_settings

if typing.TYPE_CHECKING:
    from maize.base.interface.sync_standard_spider_interface import SyncStandardSpiderInterface
    from maize.settings import SpiderSettings


class SyncCrawler:
    """同步爬虫运行器（单个 Spider）。"""

    def __init__(self, spider_cls: "SyncStandardSpiderInterface", settings: "SpiderSettings"):
        self.spider_cls = spider_cls
        self.settings: SpiderSettings = settings
        self.spider: SyncStandardSpiderInterface | None = None
        self.engine: SyncEngine | None = None

    def crawl(self):
        """启动爬虫：设置上下文 → 创建 Spider → open → 创建引擎 → start_spider → close。"""
        # 设置 settings 到上下文中，这样后续调用 get_logger() 时可以自动获取
        set_spider_settings(self.settings)

        self.spider = self._create_spider()
        self.spider.open()

        self.engine = self._create_engine()
        self.engine.start_spider(self.spider)  # type: ignore[arg-type]

        self.spider.close()

    def _create_spider(self) -> "SyncStandardSpiderInterface":
        """创建 Spider 实例并注入 custom_settings。"""
        spider = self.spider_cls.create_instance(self)
        self._set_spider(spider)
        return spider  # type: ignore[no-any-return]

    def _create_engine(self):
        return SyncEngine(self)

    def _set_spider(self, spider: "SyncStandardSpiderInterface"):
        """合并 Spider 的 custom_settings 到 settings。"""
        if hasattr(spider, "custom_settings") and spider.custom_settings and isinstance(spider.custom_settings, dict):
            self.settings.merge_settings_from_dict(spider.custom_settings)

    def idle(self) -> bool:
        if self.spider is None:
            return True
        return self.spider.idle()


class SyncCrawlerProcess:
    """
    同步爬虫运行器（支持多个 Spider）。

    与异步版 ``CrawlerProcess`` 对应，``crawl`` 注册 Spider，``start`` 依次运行。
    """

    def __init__(
        self,
        settings: typing.Optional["SpiderSettings"] = None,
        settings_path: str | None = "settings.Settings",
    ):
        self._active: typing.Final[list[SyncCrawler]] = []
        self.settings: SpiderSettings = settings if settings else self.__get_settings(settings_path)

        self.logger = get_logger(self.settings, self.__class__.__name__)

    @staticmethod
    def __get_settings(settings_path: str | None) -> "SpiderSettings":
        """获取配置。"""
        try:
            return get_settings(settings_path)  # type: ignore[arg-type]
        except (ModuleNotFoundError, NameError, TypeError) as e:
            logging.warning(f"{e} use default settings")
            return get_settings()

    def crawl(self, spider: typing.Union[typing.Type["SyncStandardSpiderInterface"], "SyncStandardSpiderInterface"]):
        """
        装配爬虫。

        :param spider: Spider 类或实例
        """
        crawler: SyncCrawler = self._create_crawler(spider)  # type: ignore[arg-type]
        self._active.append(crawler)

    def start(self):
        """依次运行所有已装配的爬虫（同步阻塞）。"""
        for crawler in self._active:
            crawler.crawl()

    def _create_crawler(self, spider_cls: "SyncStandardSpiderInterface") -> SyncCrawler:
        if isinstance(spider_cls, str):
            raise SpiderTypeException(f"{type(self)}.crawl args: String is not supported")

        return SyncCrawler(spider_cls, self.settings)
