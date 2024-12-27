from dataclasses import dataclass
from dataclasses import field

from maize.settings.spider_settings import SpiderSettings


class TestSpiderSettings:
    def test_base_settings(self):
        spider_settings = SpiderSettings()
        assert spider_settings.CONCURRENCY == 1

    def test_get_dict(self):
        spider_settings = SpiderSettings()
        spider_settings_dict = spider_settings.get_dict()
        assert isinstance(spider_settings_dict, dict)

    def test_from_json(self):
        json_data = '{"CONCURRENCY": 5, "DOWNLOADER": "custom.Downloader", "ITEM_PIPELINES": ["custom.Pipeline1", "custom.Pipeline2"]}'
        settings_from_json = SpiderSettings.from_json(json_data)
        print("From JSON:", settings_from_json.ITEM_PIPELINES)

    def test_from_base_model(self):
        @dataclass
        class CustomSpiderSettings(SpiderSettings):
            CONCURRENCY: int = 5
            DOWNLOADER: str = "custom.Downloader"
            ITEM_PIPELINES: list = field(
                default_factory=lambda: ["custom.Pipeline1", "custom.Pipeline2"]
            )

        custom_spider_settings = CustomSpiderSettings()
        assert custom_spider_settings.CONCURRENCY == 5

    def test_from_base_model_from_dict(self):
        @dataclass
        class CustomSpiderSettings(SpiderSettings):
            CONCURRENCY: int = 5
            DOWNLOADER: str = "custom.Downloader"
            ITEM_PIPELINES: list = field(
                default_factory=lambda: ["custom.Pipeline1", "custom.Pipeline2"]
            )

        custom_spider_settings = CustomSpiderSettings()
        assert custom_spider_settings.CONCURRENCY == 5

        custom_settings = {
            "PROJECT_NAME": "百度爬虫",
            "USE_REDIS": True,
            "REDIS_HOST": "192.168.137.219",
            "REDIS_PORT": 6379,
            "REDIS_DB": 0,
            "REDIS_USERNAME": None,
            "REDIS_PASSWORD": "123456",
        }
        custom_spider_settings = custom_spider_settings.from_dict(
            {
                "CONCURRENCY": 10,
                "DOWNLOADER": "custom.Downloader",
                "ITEM_PIPELINES": ["custom.Pipeline1", "custom.Pipeline2"],
            }
        )
        print("---> ", custom_spider_settings)

        custom_spider_settings.update_from_dict(custom_settings)
        assert custom_spider_settings.CONCURRENCY == 10
        print(custom_spider_settings)
        print(custom_spider_settings.ITEM_PIPELINES)
