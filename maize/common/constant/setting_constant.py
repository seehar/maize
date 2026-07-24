"""
爬虫设置相关枚举常量。

定义下载器类型、日志级别、管道类型和 RPA 配置等枚举，
供 :class:`~maize.base.settings.SpiderSettings` 及引擎组件引用。
"""

from enum import Enum, unique


@unique
class SpiderDownloaderEnum(str, Enum):
    """
    异步爬虫下载器枚举。

    每个成员的值为下载器类的完整导入路径，
    引擎通过该路径动态加载对应的下载器实现。
    """

    AIOHTTP = "maize.AioHttpDownloader"
    HTTPX = "maize.HTTPXDownloader"
    PLAYWRIGHT = "maize.downloader.playwright_downloader.PlaywrightDownloader"
    PATCHRIGHT = "maize.downloader.patchright_downloader.PatchrightDownloader"


@unique
class SyncSpiderDownloaderEnum(str, Enum):
    """
    同步爬虫下载器枚举。
    """

    HTTPX = "maize.sync.classic.downloader.sync_httpx_downloader.SyncHttpxDownloader"
    REQUESTS = "maize.sync.classic.downloader.sync_requests_downloader.SyncRequestsDownloader"


@unique
class LogLevelEnum(str, Enum):
    """
    日志级别枚举。

    与 Python :mod:`logging` 模块的标准级别一一对应。
    """

    CRITICAL = "CRITICAL"
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
    DEBUG = "DEBUG"
    NOTSET = "NOTSET"


@unique
class PipelineEnum(str, Enum):
    """
    异步爬虫管道枚举。

    每个成员的值为管道类的完整导入路径，
    引擎通过该路径动态加载对应的管道实现。
    """

    EMPTY = "maize.EmptyPipeline"
    MYSQL = "maize.MysqlPipeline"


@unique
class SyncPipelineEnum(str, Enum):
    """
    同步爬虫管道枚举。
    """

    EMPTY = "maize.sync.classic.pipeline.sync_empty_pipeline.SyncEmptyPipeline"


@unique
class RPAResourceTypeEnum(str, Enum):
    """
    RPA 资源类型枚举。
    """

    DOCUMENT = "document"
    STYLESHEET = "stylesheet"
    IMAGE = "image"
    MEDIA = "media"
    FONT = "font"
    SCRIPT = "script"
    TEXTTRACK = "texttrack"
    XHR = "xhr"
    FETCH = "fetch"
    EVENTSOURCE = "eventsource"
    WEBSOCKET = "websocket"
    MANIFEST = "manifest"
    OTHER = "other"


@unique
class RPADriverTypeEnum(str, Enum):
    """
    RPA 浏览器驱动类型枚举。
    """

    CHROMIUM = "chromium"
    FIREFOX = "firefox"
    WEBKIT = "webkit"


@unique
class RPAWaitUntilEnum(str, Enum):
    """
    RPA 页面加载等待策略枚举。
    """

    COMMIT = "commit"  # 仅等待导航完成
    DOMCONTENTLOADED = "domcontentloaded"  # DOM加载完成
    LOAD = "load"  # 等待所有资源加载完成
    NETWORKIDLE = "networkidle"  # 等待网络空闲
