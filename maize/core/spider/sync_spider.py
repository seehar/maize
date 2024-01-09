import multiprocessing
import typing

from requests import Response

from maize.core.downloader import SyncDownloader
from maize.core.interface import SpiderInterface
from maize.models import DownLoaderModel
from maize.models.enums import SpiderStatus
from maize.utils.logger_util import logger


class SyncSpider(SpiderInterface):
    def __init__(
        self,
        downloader: typing.Type[SyncDownloader] = SyncDownloader,
        process_num: int = 1,
    ):
        super().__init__()
        self._downloader = downloader()
        self.process_num = process_num

    def start(self):
        for _task in self.make_requests():
            if isinstance(_task, dict):
                _task = DownLoaderModel(**_task)
            self.task_list.append(_task)

        self.status = SpiderStatus.RUNNING
        self.download(self.task_list)
        self.finish()

    def download(self, task_list: typing.List[typing.Union[DownLoaderModel, dict]]):
        with multiprocessing.Pool(processes=self.process_num) as pool:
            results = pool.map(self._process_download_task, task_list)
            return results

    def stop(self):
        self.status = SpiderStatus.STOPPED

    def finish(self):
        self.status = SpiderStatus.COMPLETED

    def _process_download_task(self, task: DownLoaderModel) -> Response:
        logger.info(f"正在下载: {task.json()}")
        response = self._downloader.download(url=task.url, headers=task.headers)
        logger.info(f"下载完成: {task.url} {response.status_code}")

        parse_result = self.parse(task, response)
        logger.info(f"最终结果: {parse_result}")
        return parse_result

    def make_requests(self):
        pass

    def parse(self, task: DownLoaderModel, response: Response):
        return response
