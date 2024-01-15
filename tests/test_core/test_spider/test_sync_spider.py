import logging

from requests import Response

from maize import SyncSpider
from maize.models import DownLoaderModel


class SimpleSpider(SyncSpider):
    def make_requests(self):
        yield {"url": "http://www.seehar.com"}

    def parse(self, task: DownLoaderModel, response: Response) -> str:
        logging.info(f"开始解析: {task.url}")
        result = response.text[:100]
        logging.info(f"解析完成: {task.url}")
        return result

    def verify(self, task: DownLoaderModel, response: Response) -> bool:
        return "seehar" in response.text


class MultiprocessSpider(SyncSpider):
    def make_requests(self):
        for i in range(10):
            yield {"url": "http://www.seehar.com"}

    def parse(self, task: DownLoaderModel, response: Response) -> str:
        logging.info(f"开始解析: {task.url}")
        result = response.text[:100]
        logging.info(f"解析完成: {task.url}")
        return result


class TestSyncSpider:
    def test_success_spider(self):
        spider = SimpleSpider()
        spider.start()

    def test_multiprocess_spider(self):
        spider = MultiprocessSpider(process_num=2)
        spider.start()
