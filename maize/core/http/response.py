import re
import typing
from http.cookies import SimpleCookie
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
        """
        响应
        @param url: url
        @param headers: 响应头
        @param request: 请求 Response
        @param body: 响应体 bytes 类型
        @param status: 响应状态码，如 200
        """
        self.url = url
        self.request = request
        self.headers = headers
        self.body = body
        self.status = status
        self.encoding = request.encoding

        self._text_cache: typing.Optional[str] = None
        self._cookies_list_cache: typing.Optional[list[dict]] = None
        self._cookies_cache: typing.Optional[list[dict]] = None
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

    @property
    def cookies_list(self):
        if self._cookies_list_cache:
            return self._cookies_list_cache

        set_cookie_header = self.headers.get("Set-Cookie", "")

        cookie_obj = SimpleCookie()
        cookie_obj.load(set_cookie_header)

        self._cookies_list_cache = [
            {
                "key": key,
                "value": morsel.value,
                "domain": morsel.get("domain", ""),
                "path": morsel.get("path", ""),
                "expires": morsel.get("expires", ""),
                "secure": morsel.get("secure", ""),
                "httponly": morsel.get("httponly", ""),
            }
            for key, morsel in cookie_obj.items()
        ]

        return self._cookies_list_cache

    @property
    def cookies(self):
        if self._cookies_cache:
            return self._cookies_cache

        self._cookies_cache = {
            cookie["key"]: cookie["value"] for cookie in self.cookies_list
        }
        return self._cookies_cache

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
