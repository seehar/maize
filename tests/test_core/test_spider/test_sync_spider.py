import pytest
from requests import Response

from maize import SyncSpider
from maize.models import DownLoaderModel
from maize.utils.logger_util import logger


class SimpleSpider(SyncSpider):
    def make_requests(self):
        yield {"url": "https://www.baidu.com"}

    def parse(self, task: DownLoaderModel, response: Response) -> str:
        logger.info(f"开始解析: {task.url}")
        result = response.text[:100]
        logger.info(f"解析完成: {task.url}")
        return result


class MultiprocessSpider(SyncSpider):
    def make_requests(self):
        for i in range(10):
            yield {"url": "https://www.baidu.com"}

    def parse(self, task: DownLoaderModel, response: Response) -> str:
        logger.info(f"开始解析: {task.url}")
        result = response.text[:100]
        logger.info(f"解析完成: {task.url}")
        return result


class TestSyncSpider:
    @pytest.mark.skip("")
    def test_success_spider(self):
        spider = SimpleSpider()
        spider.start()

    @pytest.mark.skip("")
    def test_multiprocess_spider(self):
        spider = MultiprocessSpider(process_num=2)
        spider.start()
