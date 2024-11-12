# 配置文件

配置文件位于 `project/settings.py`，与 `run.py` 或 `settings.py` 同级。
同样的，也可以在 `Spider` 中的 `custom_settings` 中进行设置，优先级高于 `settings.py`。


```python
from maize import Spider


class CustomSpider(Spider):
    custom_settings = {
        # 并发数
        'CONCURRENCY': 2,

        # 是否验证 SSL 证书
        'VERIFY_SSL': False,

        # 请求超时时间
        'REQUEST_TIMEOUT': 30,

        # 是否使用 session
        'USE_SESSION': False,
        
        # ...
    }
    
    # ...
```

或者自定义 `Settings` 类。您可以继承 `BaseSettings` 或者不继承，具体请看下面的示例。
如果您继承了 `BaseSettings`，那么您可以获得更好的代码提示。如果您不继承，那么您需要注意，不要将配置项命名写错。

=== "继承 `BaseSettings`"
    ```python
    from maize import BaseSettings
    
    
    class Settings(BaseSettings):
        CONCURRENCY = 1
        ...
    ```

=== "不继承 `BaseSettings`"
    ```python
    class Settings:
        CONCURRENCY = 1
        ...
    ```

默认配置如下：


```python
class BaseSettings:
    # 并发数
    CONCURRENCY: int = 1

    # 是否验证 SSL 证书
    VERIFY_SSL: bool = True

    # 请求超时时间
    REQUEST_TIMEOUT: int = 60

    # 是否使用 session
    # 注意：基于 httpx 的下载器（HTTPXDownloader）不支持 session，所以此选项无效
    USE_SESSION: bool = True

    # 下载器
    # 基于 aiohttp 封装的下载器：maize.AioHttpDownloader
    # 基于 httpx 封装的下载器：maize.HTTPXDownloader
    DOWNLOADER: str = "maize.AioHttpDownloader"

    # 日志级别，与 logging 日志级别相同
    # 如果您使用自定义日志处理模块，此选项无效，请您在自定义日志处理模块中设置日志级别
    LOG_LEVEL: str = "INFO"

    # # 日志 handler
    # # 如不想使用默认的 logging 模块，可以自定义日志处理模块
    # LOGGER_HANDLER: str = ""

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
    ITEM_PIPELINES: list[str] = ["maize.BasePipeline"]

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
    RPA_USER_AGENT: Optional[str] = None

    # 窗口大小
    RPA_WINDOW_SIZE: Tuple[int, int] = (1024, 800)

    # 浏览器路径，默认为默认路径
    RPA_EXECUTABLE_PATH: Optional[str] = None

    # 下载文件的路径
    RPA_DOWNLOAD_PATH: Optional[str] = None

    # 渲染时长，即打开网页等待指定时间后再获取源码
    RPA_RENDER_TIME: Optional[int] = None

    # 自定义浏览器渲染参数
    RPA_CUSTOM_ARGUMENT: List[str] = []

    # 是否使用分布式爬虫，开启后，需要对 redis 进行配置
    IS_DISTRIBUTED: bool = False

    # redis
    USE_REDIS: bool = False
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_USERNAME: Optional[str] = None
    REDIS_PASSWORD: Optional[str] = None

    REDIS_KEY_PREFIX: str = "maize"
    REDIS_KEY_LOCK: str = "lock"
    REDIS_KEY_RUNNING: str = "running"
    REDIS_KEY_QUEUE: str = "queue"

    # # 隧道代理，示例：xxx.xxx:2132。注意：不包含 http:// 或 https://
    # PROXY_TUNNEL: str = ""
    #
    # # 隧道代理用户名
    # PROXY_TUNNEL_USERNAME: str = ""
    #
    # # 隧道代理密码
    # PROXY_TUNNEL_PASSWORD: str = ""

    # # mysql数据库配置
    # MYSQL_HOST: str = "localhost"
    # MYSQL_PORT: str | int = 3306
    # MYSQL_DB: str = ""
    # MYSQL_USER: str = ""
    # MYSQL_PASSWORD: str = ""
```
