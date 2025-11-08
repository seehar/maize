from enum import Enum
from enum import unique


@unique
class SpiderDownloaderEnum(str, Enum):
    AIOHTTP = "maize.AioHttpDownloader"
    HTTPX = "maize.HTTPXDownloader"
    PLAYWRIGHT = "maize.downloader.playwright_downloader.PlaywrightDownloader"


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
    BASE = "maize.BasePipeline"
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
