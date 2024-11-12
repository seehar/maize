from maize import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME = "baidu_spider"
    CONCURRENCY = 1
    LOG_LEVEL = "DEBUG"

    DOWNLOADER = "maize.HTTPXDownloader"

    LOGGER_HANDLER = "examples.baidu_spider.logger_util.InterceptHandler"

    # ITEM_PIPELINES = ["examples.baidu_spider.pipeline.CustomPipeline"]

    # MYSQL_HOST = "localhost"
    # MYSQL_PORT = 3306
    # MYSQL_USER = "root"
    # MYSQL_PASSWORD = "123456"
    # MYSQL_DB = "maize"

    # redis
    REDIS_HOST: str = "192.168.137.219"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_USERNAME = None
    REDIS_PASSWORD = "123456"
