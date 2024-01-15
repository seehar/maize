import logging
import multiprocessing
import typing

from requests import Response

from maize.core.downloader import SyncDownloader
from maize.core.interface import SpiderInterface
from maize.exceptions import ResponseVerifyException
from maize.models import DownLoaderModel
from maize.models.enums import SpiderStatus


class SyncSpider(SpiderInterface):
    def __init__(
        self,
        downloader: type[SyncDownloader] = SyncDownloader,
        process_num: int = 1,
    ):
        super().__init__()
        self._downloader = downloader()
        self.process_num = process_num

    def start(self):
        """
        启动爬虫
        :return:
        """
        for _task in self.make_requests():
            if isinstance(_task, dict):
                _task = DownLoaderModel(**_task)
            self.task_list.append(_task)

        self.status = SpiderStatus.RUNNING
        self.download(self.task_list)
        self.finish()

    def stop(self):
        """
        主动停止爬虫
        :return:
        """
        self.status = SpiderStatus.STOPPED

    def finish(self):
        """
        爬虫完成
        :return:
        """
        self.status = SpiderStatus.COMPLETED

    def make_requests(
        self,
    ) -> typing.Generator[
        typing.Union[dict[str, str], DownLoaderModel], typing.Any, None
    ]:
        """
        生成请求
        :return:
        """

    def parse(self, task: DownLoaderModel, response: Response):
        """
        解析响应
        :param task:
        :param response:
        :return:
        """
        return response

    def download(self, task_list: list[typing.Union[DownLoaderModel, dict]]):
        """
        多进程下载任务
        :param task_list:
        :return:
        """
        with multiprocessing.Pool(processes=self.process_num) as pool:
            results = pool.map(self._process_download_task, task_list)
            return results

    def _process_download_task(self, task: DownLoaderModel):
        """
        下载任务处理
        :param task:
        :return:
        """
        response = self.__download_and_verify(task)
        parse_result = self.parse(task, response)
        logging.info(f"最终结果: {parse_result}")
        return parse_result

    def __download_and_verify(self, task: DownLoaderModel) -> Response:
        """
        下载并进行自定义校验
        :param task:
        :return:
        """
        logging.info(f"正在下载: {task.json()}")
        response = self._downloader.download(url=task.url, headers=task.headers)

        if not self.verify(task, response):
            self.handle_exception(task, ResponseVerifyException)
            raise ResponseVerifyException("自定义响应校验错误")

        logging.info(f"下载完成: {task.url} {response.status_code}")
        return response

    def verify(self, task: DownLoaderModel, response: Response) -> bool:
        """
        自定义响应校验，
        如果校验失败，返回False或抛出异常，则不会进行后续的解析操作。将会开始重试
        :param task:
        :param response:
        :return:
        """
        return True

    def handle_exception(
        self, task: DownLoaderModel, exception: typing.Type[Exception]
    ):
        """
        处理各种可能会遇到的异常，或者 verify 中被抛出的异常
        :param task:
        :param exception:
        :return:
        """
        print(f"Download failed for {task}")
        print(exception)
