from maize.core.interface import SpiderInterface
from maize.models.enums import SpiderStatus


class SyncSpider(SpiderInterface):
    # def __init__(self, downloader: DownloadInterface, parser: ParserInterface, middleware: MiddlewareInterface,
    #              pipeline: PipelineInterface):
    #     super().__init__(downloader, parser, middleware, pipeline)

    def start(self):
        self.status = SpiderStatus.RUNNING

    def stop(self):
        ...
