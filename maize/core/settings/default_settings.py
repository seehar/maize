"""
default config
"""

# 并发数
CONCURRENCY = 16

FLAG = True

# 是否验证 SSL 证书
VERIFY_SSL = True

# 请求超时时间
REQUEST_TIMEOUT = 60

# 是否使用 session
USE_SESSION = True

# 下载器
DOWNLOADER = "maize.AioHttpDownloader"

# 日志级别
LOG_LEVEL = "INFO"

# 日志 handler
LOGGER_HANDLER = ""
