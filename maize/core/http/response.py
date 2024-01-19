import re
import typing
from urllib.parse import urljoin as _urljoin

import ujson
from parsel import Selector
from parsel import SelectorList

from maize.core.http.request import Request
from maize.exceptions.spider_exception import DecodeException


class Response:
    def __init__(
        self,
        url: str,
        *,
        headers: dict,
        request: Request,
        body: bytes = b"",
        status: int = 200,
    ):
        self.url = url
        self.request = request
        self.headers = headers
        self.body = body
        self.status = status
        self.encoding = request.encoding

        self._text_cache: typing.Optional[str] = None
        self._selector: typing.Optional[Selector] = None

    @property
    def text(self):
        if self._text_cache:
            return self._text_cache

        try:
            self._text_cache = self.body.decode(self.encoding)
        except UnicodeDecodeError:
            try:
                _encoding_re = re.compile(r"charset=([\w-]+)", flags=re.I)
                _encoding_string = self.headers.get(
                    "Content-Type", ""
                ) or self.headers.get("content-type", "")
                _encoding = _encoding_re.search(_encoding_string)
                if _encoding:
                    _encoding = _encoding.group(1)
                    self._text_cache = self.body.decode(_encoding)
                else:
                    raise DecodeException(
                        f"{self.request} {self.request.encoding} error."
                    )
            except UnicodeDecodeError as e:
                raise DecodeException(
                    e.encoding, e.object, e.start, e.end, f"{self.request}"
                )
        return self._text_cache

    def json(self) -> dict:
        return ujson.loads(self.text)

    def urljoin(self, url: str) -> str:
        return _urljoin(self.url, url)

    def xpath(self, xpath: str) -> SelectorList[Selector]:
        if self._selector is None:
            self._selector = Selector(self.text)

        return self._selector.xpath(xpath)

    def __str__(self):
        return f"<{self.status}> {self.url}"

    @property
    def meta(self) -> dict:
        return self.request.meta
