PROJECT_NAME = "baidu_spider"
CONCURRENCY = 1
LOG_LEVEL = "DEBUG"

DOWNLOADER = "maize.HTTPXDownloader"

LOGGER_HANDLER = "tests.test_full_process.logger_util.InterceptHandler"

ITEM_PIPELINES = ["tests.test_full_process.pipeline.CustomPipeline"]

# # mysql数据库配置
# MYSQL_HOST = ""
# MYSQL_PORT = 3306
# MYSQL_DB = ""
# MYSQL_USER = ""
# MYSQL_PASSWORD = ""
