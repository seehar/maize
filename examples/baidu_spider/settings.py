from maize import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME = "baidu_spider"
    CONCURRENCY = 1
    LOG_LEVEL = "DEBUG"

    DOWNLOADER = "maize.HTTPXDownloader"

    LOGGER_HANDLER = "examples.baidu_spider.logger_util.InterceptHandler"

    from examples.baidu_spider.pipeline import CustomPipeline

    ITEM_PIPELINES = ["examples.baidu_spider.pipeline.CustomPipeline"]

    MYSQL_HOST = "localhost"
    MYSQL_PORT = 3306
    MYSQL_USER = "root"
    MYSQL_PASSWORD = "123456"
    MYSQL_DB = "maize"
