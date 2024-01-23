import typing

from maize.core.http.request import Request
from maize.core.http.response import Response


if typing.TYPE_CHECKING:
    from maize.core.crawler import Crawler


class Spider:
    start_urls: list[str] = []
    start_url: typing.Optional[str] = None

    custom_settings: dict

    def __init__(self):
        if not hasattr(self, "start_urls"):
            self.start_urls = []

        self.crawler: typing.Optional["Crawler"] = None

    @classmethod
    def create_instance(cls, crawler: "Crawler"):
        instance = cls()
        instance.crawler = crawler
        return instance

    def start_requests(self) -> typing.Generator[Request, typing.Any, None]:
        if self.start_urls:
            for url in self.start_urls:
                yield Request(url=url)

        elif self.start_url and isinstance(self.start_url, str):
            yield Request(url=self.start_url)

    def parse(self, response: Response):
        raise NotImplementedError

    def __str__(self):
        return self.__class__.__name__
