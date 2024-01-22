"""
default config
"""

# 并发数
CONCURRENCY = 1

# 是否验证 SSL 证书
VERIFY_SSL = True

# 请求超时时间
REQUEST_TIMEOUT = 60

# 是否使用 session
USE_SESSION = True

# 下载器
# 基于 aiohttp 封装的下载器：maize.AioHttpDownloader
# 基于 httpx 封装的下载器：maize.HTTPXDownloader
DOWNLOADER = "maize.AioHttpDownloader"

# 日志级别，与 logging 日志级别相同
LOG_LEVEL = "INFO"

# 日志 handler
# 如不想使用默认的 logging 模块，可以自定义日志处理模块
LOGGER_HANDLER = ""

# 最大重试次数
MAX_RETRY_COUNT = 0

# item在内存队列中最大缓存数量
ITEM_MAX_CACHE_COUNT = 5000

# item每批入库的最大数量
ITEM_HANDLE_BATCH_MAX_SIZE = 1000

# item入库时间间隔，单位：秒
ITEM_HANDLE_INTERVAL = 2

# 数据管道，默认 BasePipeline 不做任何处理
ITEM_PIPELINES = ["maize.BasePipeline"]
