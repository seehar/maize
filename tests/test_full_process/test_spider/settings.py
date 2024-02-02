from maize import BaseSettings


class SpiderSettings(BaseSettings):
    PROJECT_NAME = "baidu_spider"
    CONCURRENCY = 1
    LOG_LEVEL = "DEBUG"
    DOWNLOADER = "maize.HTTPXDownloader"
    LOGGER_HANDLER = "tests.test_full_process.test_spider.logger_util.InterceptHandler"

    ITEM_PIPELINES = ["tests.test_full_process.test_spider.pipeline.CustomPipeline"]
