from maize import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME = "baidu_spider"
    CONCURRENCY = 1
    LOG_LEVEL = "DEBUG"

    DOWNLOADER = "maize.HTTPXDownloader"

    LOGGER_HANDLER = "examples.baidu_spider.logger_util.InterceptHandler"
