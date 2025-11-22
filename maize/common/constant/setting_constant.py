from enum import Enum, unique


@unique
class SpiderDownloaderEnum(str, Enum):
    AIOHTTP = "maize.AioHttpDownloader"
    HTTPX = "maize.HTTPXDownloader"
    PLAYWRIGHT = "maize.downloader.playwright_downloader.PlaywrightDownloader"
    PATCHRIGHT = "maize.downloader.patchright_downloader.PatchrightDownloader"


@unique
class LogLevelEnum(str, Enum):
    CRITICAL = "CRITICAL"
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
    DEBUG = "DEBUG"
    NOTSET = "NOTSET"


@unique
class PipelineEnum(str, Enum):
    EMPTY = "maize.EmptyPipeline"
    MYSQL = "maize.MysqlPipeline"


@unique
class RPAResourceTypeEnum(str, Enum):
    """RPA 资源类型枚举"""

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
    """RPA 浏览器驱动类型枚举"""

    CHROMIUM = "chromium"
    FIREFOX = "firefox"
    WEBKIT = "webkit"


@unique
class RPAWaitUntilEnum(str, Enum):
    """RPA 页面加载等待策略枚举"""

    COMMIT = "commit"  # 仅等待导航完成
    DOMCONTENTLOADED = "domcontentloaded"  # DOM加载完成
    LOAD = "load"  # 等待所有资源加载完成
    NETWORKIDLE = "networkidle"  # 等待网络空闲
