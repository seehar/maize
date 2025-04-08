"""
default config
"""
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import List
from typing import Literal
from typing import Optional
from typing import Tuple

from maize.common.model.base_model import BaseModel


BASE_DIR = Path(__file__).parent.parent


@dataclass
class SpiderSettings(BaseModel):
    PROJECT_NAME: str = "project name"

    # 并发数
    CONCURRENCY: int = 1

    # 是否验证 SSL 证书
    VERIFY_SSL: bool = True

    # 请求超时时间，单位：秒
    REQUEST_TIMEOUT: int = 60

    # 随机等待时间，单位：秒
    RANDOM_WAIT_TIME: Tuple[int, int] = (0, 0)

    # 是否使用 session
    # 注意：基于 httpx 的下载器（HTTPXDownloader）不支持 session，所以此选项无效
    USE_SESSION: bool = True

    # 下载器
    # 基于 aiohttp 封装的下载器：maize.AioHttpDownloader
    # 基于 httpx 封装的下载器：maize.HTTPXDownloader
    # 基于 playwright 封装的下载器: maize.downloader.playwright_downloader.PlaywrightDownloader
    DOWNLOADER: str = "maize.AioHttpDownloader"

    # 日志级别，与 logging 日志级别相同
    # 如果您使用自定义日志处理模块，此选项无效，请您在自定义日志处理模块中设置日志级别
    LOG_LEVEL: str = "INFO"

    # 日志 handler
    # 如不想使用默认的 logging 模块，可以自定义日志处理模块
    LOGGER_HANDLER: str = ""

    # 请求最大重试次数
    MAX_RETRY_COUNT: int = 0

    # item在内存队列中最大缓存数量
    ITEM_MAX_CACHE_COUNT: int = 5000

    # item每批入库的最大数量
    ITEM_HANDLE_BATCH_MAX_SIZE: int = 1000

    # item入库时间间隔，单位：秒
    ITEM_HANDLE_INTERVAL: int = 2

    # 入库异常的 item 最大重试次数
    ERROR_ITEM_MAX_RETRY_COUNT: int = 5

    # 入库异常的 item 在内存队列中最大缓存数量
    ERROR_ITEM_MAX_CACHE_COUNT: int = 5000

    # 入库异常的 item 重试每批处理的最大数量
    # 批量入库可能会因为某个 item 异常，导致整批数据无法入库，建议每批处理一个 item
    ERROR_ITEM_RETRY_BATCH_MAX_SIZE: int = 1

    # 入库异常的 item 超过重试次数后，每批处理的最大数量
    ERROR_ITEM_HANDLE_BATCH_MAX_SIZE: int = 1000

    # 处理入库异常的 item 时间间隔，单位：秒
    ERROR_ITEM_HANDLE_INTERVAL: int = 60

    # 数据管道，支持多个数据管道
    # maize.BasePipeline: 默认数据管道，不做任何处理
    # maize.MysqlPipeline: 集成 aiomysql 的数据管道，自动入库 mysql 数据库
    ITEM_PIPELINES: List[str] = field(default_factory=lambda: ["maize.BasePipeline"])

    # rpa
    # 使用使用 stealth js
    RPA_USE_STEALTH_JS: bool = True
    # stealth js 文件路径
    RPA_STEALTH_JS_PATH: Path = BASE_DIR / "utils/js/stealth.min.js"

    # 是否为无头浏览器
    RPA_HEADLESS: bool = True

    # chromium、firefox、webkit
    RPA_DRIVER_TYPE: Literal["chromium", "firefox", "webkit"] = "chromium"

    # 请求头
    RPA_USER_AGENT: Optional[str] = field(default_factory=lambda: None)

    # # 窗口大小
    RPA_WINDOW_SIZE: Tuple[int, int] = field(default_factory=lambda: (1024, 800))

    # 浏览器路径，默认为默认路径
    RPA_EXECUTABLE_PATH: Optional[str] = field(default_factory=lambda: None)

    # 下载文件的路径
    RPA_DOWNLOAD_PATH: Optional[str] = field(default_factory=lambda: None)

    # 渲染时长，即打开网页等待指定时间后再获取源码
    RPA_RENDER_TIME: Optional[int] = field(default_factory=lambda: None)

    # 自定义浏览器渲染参数
    RPA_CUSTOM_ARGUMENT: List[str] = field(
        default_factory=lambda: ["--no-sandbox", "--disable-blink-features=AutomationControlled"]
    )

    # 要连接的 CDP websocket 端点或 http url。例如 `http://localhost:9222/` 或
    # `ws://127.0.0.1:9222/devtools/browser/387adf4c-243f-4051-a181-46798f4a46f4`.
    RPA_ENDPOINT_URL: Optional[str] = field(default_factory=lambda: None)

    # 将 RPA 操作减慢指定的毫秒数。很有用，这样您就可以看到发生了什么。默认为0。
    RPA_SLOW_MO: Optional[float] = field(default_factory=lambda: None)

    # 是否使用分布式爬虫，开启后，需要对 redis 进行配置
    IS_DISTRIBUTED: bool = False

    # 拦截 xhr 接口，支持正则，数组类型
    RPA_URL_REGEXES: List[str] = field(default_factory=lambda: [])

    # 是否保存所有拦截的接口, 配合 url_regexes 使用，为 False 时只保存最后一次拦截的接口
    RPA_URL_REGEXES_SAVE_ALL: bool = False

    # redis
    USE_REDIS: bool = False
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_USERNAME: Optional[str] = field(default_factory=lambda: None)
    REDIS_PASSWORD: Optional[str] = field(default_factory=lambda: None)

    REDIS_KEY_PREFIX: str = "maize"
    REDIS_KEY_LOCK: str = "lock"
    REDIS_KEY_RUNNING: str = "running"
    REDIS_KEY_QUEUE: str = "queue"

    # 隧道代理，示例：xxx.xxx:2132。注意：不包含 http:// 或 https://
    PROXY_TUNNEL: str = ""

    # 隧道代理用户名
    PROXY_TUNNEL_USERNAME: str = ""

    # 隧道代理密码
    PROXY_TUNNEL_PASSWORD: str = ""

    # mysql数据库配置
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: str | int = 3306
    MYSQL_DB: str = ""
    MYSQL_USER: str = ""
    MYSQL_PASSWORD: str = ""

    @property
    def redis_url(self):
        redis_url_username_password = ""
        if self.REDIS_USERNAME or self.REDIS_PASSWORD:
            redis_url_username_password = f"{self.REDIS_USERNAME or ''}:{self.REDIS_PASSWORD or ''}@"

        return f"redis://{redis_url_username_password}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
