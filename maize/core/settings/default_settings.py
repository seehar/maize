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
# 注意：基于 httpx 的下载器（HTTPXDownloader）不支持 session，所以此选项无效
USE_SESSION = True

# 下载器
# 基于 aiohttp 封装的下载器：maize.AioHttpDownloader
# 基于 httpx 封装的下载器：maize.HTTPXDownloader
DOWNLOADER = "maize.AioHttpDownloader"

# 日志级别，与 logging 日志级别相同
# 如果您使用自定义日志处理模块，此选项无效，请您在自定义日志处理模块中设置日志级别
LOG_LEVEL = "INFO"

# # 日志 handler
# # 如不想使用默认的 logging 模块，可以自定义日志处理模块
# LOGGER_HANDLER = ""

# 最大重试次数
MAX_RETRY_COUNT = 0

# item在内存队列中最大缓存数量
ITEM_MAX_CACHE_COUNT = 5000

# item每批入库的最大数量
ITEM_HANDLE_BATCH_MAX_SIZE = 1000

# item入库时间间隔，单位：秒
ITEM_HANDLE_INTERVAL = 2

# # 数据管道，支持多个数据管道
# # maize.BasePipeline: 默认数据管道，不做任何处理
# # maize.MysqlPipeline: 集成 aiomysql 的数据管道，自动入库 mysql 数据库
# ITEM_PIPELINES = ["maize.BasePipeline"]

# # 隧道代理，示例：xxx.xxx:2132。注意：不包含 http:// 或 https://
# PROXY_TUNNEL = ""
#
# # 隧道代理用户名
# PROXY_TUNNEL_USERNAME = ""
#
# # 隧道代理密码
# PROXY_TUNNEL_PASSWORD = ""

# # mysql数据库配置
# MYSQL_HOST = "localhost"
# MYSQL_PORT = 3306
# MYSQL_DB = ""
# MYSQL_USER = ""
# MYSQL_PASSWORD = ""
