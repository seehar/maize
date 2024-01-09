from abc import ABC
from abc import abstractmethod

from maize.models.enums import SpiderStatus

from .downloader_interface import DownloadInterface
from .middleware_interface import MiddlewareInterface
from .parser_interface import ParserInterface
from .pipeline_interface import PipelineInterface


class SpiderInterface(ABC):
    _status: SpiderStatus = SpiderStatus.DEFAULT

    def __init__(
        self,
        downloader: DownloadInterface,
        parser: ParserInterface,
        middleware: MiddlewareInterface,
        pipeline: PipelineInterface,
    ):
        self._downloader = downloader
        self._parser = parser
        self._middleware_chain = middleware
        self._pipeline_chain = pipeline

        self._status = SpiderStatus.INITIALIZED

    @abstractmethod
    def start(self):
        raise NotImplementedError

    @abstractmethod
    def stop(self):
        raise NotImplementedError

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, status):
        self._status = status

    def _task(self, task_name):
        pass

    def _complete_message(self):
        pass

    def _save_state(self):
        pass

    def _load_state(self):
        pass

    def _log_error(self, task_name, error_message):
        pass

    def _process_task(self, task_name):
        pass
