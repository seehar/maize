from abc import ABC
from abc import abstractmethod


class PipelineInterface(ABC):
    @abstractmethod
    def process_item(self, item):
        pass

    @abstractmethod
    def open_spider(self):
        pass

    @abstractmethod
    def close_spider(self):
        pass
