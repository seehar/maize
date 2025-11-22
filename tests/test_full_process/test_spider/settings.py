from pydantic import Field

from maize import SpiderSettings
from maize.common.constant.setting_constant import LogLevelEnum, SpiderDownloaderEnum
from maize.settings.spider_settings import PipelineSettings


class BaiduSpiderPipelineSettings(PipelineSettings):
    pipelines: list[str] = Field(default=["tests.test_full_process.test_spider.pipeline.CustomPipeline"])


class BaiduSpiderSettings(SpiderSettings):
    project_name: str = "baidu_spider"
    concurrency: int = 1
    log_level: str = LogLevelEnum.DEBUG.value
    downloader: str = SpiderDownloaderEnum.HTTPX.value
    logger_handler: str = "tests.test_full_process.test_spider.logger_util.InterceptHandler"
    pipeline: PipelineSettings = BaiduSpiderPipelineSettings()
