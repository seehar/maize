import ujson

from maize import Field
from maize.settings.spider_settings import PipelineSettings, SpiderSettings


class TestSpiderSettings:
    def test_base_settings(self):
        spider_settings = SpiderSettings()
        assert spider_settings.concurrency == 1

    def test_get_dict(self):
        spider_settings = SpiderSettings()
        spider_settings_dict = spider_settings.model_dump()
        assert isinstance(spider_settings_dict, dict)

    def test_from_json(self):
        json_data = '{"concurrency": 5, "downloader": "custom.Downloader", "pipeline": {"pipelines": ["custom.Pipeline1", "custom.Pipeline2"]}}'
        settings_from_json = SpiderSettings(**ujson.loads(json_data))
        print("From JSON:", settings_from_json.pipeline.pipelines)

    def test_from_base_model(self):
        class CustomPipelineSettings(PipelineSettings):
            pipelines: list[str] = Field(default=["custom.Pipeline1", "custom.Pipeline2"])

        class CustomSpiderSettings(SpiderSettings):
            concurrency: int = 5
            downloader: str = "custom.Downloader"
            pipeline: PipelineSettings = CustomPipelineSettings()

        custom_spider_settings = CustomSpiderSettings()
        assert custom_spider_settings.concurrency == 5

    def test_from_base_model_from_dict(self):
        class CustomPipelineSettings(PipelineSettings):
            pipelines: list[str] = Field(default=["custom.Pipeline1", "custom.Pipeline2"])

        class CustomSpiderSettings(SpiderSettings):
            concurrency: int = 5
            downloader: str = "custom.Downloader"
            pipeline: PipelineSettings = CustomPipelineSettings()

        custom_spider_settings = CustomSpiderSettings()
        assert custom_spider_settings.concurrency == 5

        custom_settings = {
            "project_name": "百度爬虫",
            "redis": {
                "use_redis": True,
                "redis_host": "192.168.137.219",
                "redis_port": 6379,
                "redis_db": 0,
                "redis_username": None,
                "redis_password": "123456",
            },
        }
        custom_spider_settings = CustomSpiderSettings(
            **{
                "concurrency": 10,
                "downloader": "custom.Downloader",
                "pipeline": {
                    "pipelines": ["custom.Pipeline1", "custom.Pipeline2"],
                },
            }
        )
        print("---> ", custom_spider_settings)

        custom_spider_settings.merge_settings_from_dict(custom_settings)
        assert custom_spider_settings.concurrency == 10
        print(custom_spider_settings)
        print(custom_spider_settings.pipeline.pipelines)
