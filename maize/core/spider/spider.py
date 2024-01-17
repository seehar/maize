from maize.core.http.response import Response
from maize.core.http.request import Request


class Spider:
    def __init__(self):
        if not hasattr(self, "start_urls"):
            self.start_urls = []

        self.crawler = None

    @classmethod
    def create_instance(cls, crawler):
        instance = cls()
        instance.crawler = crawler
        return instance

    def start_requests(self):
        if self.start_urls:
            for url in self.start_urls:
                yield Request(url=url)

        else:
            if hasattr(self, "start_url") and isinstance(
                getattr(self, "start_url"), str
            ):
                yield Request(url=getattr(self, "start_url"))

    def parse(self, response: Response):
        raise NotImplementedError

    def __str__(self):
        return self.__class__.__name__
