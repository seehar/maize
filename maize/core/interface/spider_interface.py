import typing
from abc import ABC
from abc import abstractmethod

from maize.models import DownLoaderModel
from maize.models.enums import SpiderStatus
from maize.utils.logger_util import logger


class SpiderInterface(ABC):
    _status: SpiderStatus = SpiderStatus.DEFAULT
    task_list: typing.List[DownLoaderModel] = []

    def __init__(self):
        self.status = SpiderStatus.INITIALIZED

    @abstractmethod
    def start(self):
        """启动爬虫"""
        raise NotImplementedError

    @abstractmethod
    def stop(self):
        """停止爬虫"""
        raise NotImplementedError

    @abstractmethod
    def finish(self):
        """完成爬虫"""
        raise NotImplementedError

    @abstractmethod
    def make_requests(
        self,
    ) -> typing.Generator[
        typing.Union[typing.Dict[str, str], DownLoaderModel], typing.Any, None
    ]:
        """生成请求"""
        raise NotImplementedError

    @abstractmethod
    def parse(self, task: DownLoaderModel, response):
        """解析响应"""
        raise NotImplementedError

    @abstractmethod
    def download(self, task_list: typing.List[DownLoaderModel]):
        """下载"""
        raise NotImplementedError

    @abstractmethod
    def _process_download_task(self, task: DownLoaderModel):
        """处理下载任务"""
        raise NotImplementedError

    @property
    def status(self):
        """获取爬虫状态"""
        return self._status

    @status.setter
    def status(self, status: SpiderStatus):
        """设置爬虫状态"""
        self._status = status
        logger.info(f"爬虫状态已更新为：{status.name}")
