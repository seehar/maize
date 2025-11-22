import re
from http.cookies import SimpleCookie
from typing import TYPE_CHECKING, Any, Generic, TypeVar, Union
from urllib.parse import urljoin as _urljoin

import ujson
from parsel import Selector, SelectorList

from maize.exceptions.spider_exception import DecodeException, EncodeException

if TYPE_CHECKING:
    from maize.common.http.request import Request

Driver = TypeVar("Driver")
R = TypeVar("R")


class Response(Generic[Driver, R]):
    def __init__(
        self,
        url: str,
        *,
        headers: dict[str, Any],
        request: "Request",
        body: bytes = b"",
        text: str = "",
        status: int = 200,
        cookie_list: list[dict[str, Union[str, bool]]] | None = None,
        driver: Driver | None = None,
        source_response: R | None = None,
    ):
        """
        响应

        :param url: url
        :param headers: 响应头
        :param request: 请求 Request
        :param body: 响应体 bytes 类型
        :param text: 响应体 str 类型
        :param status: 响应状态码，如 200
        :param cookie_list: cookie 列表
        :param driver:
        :param source_response: 原始响应，如下载器是 httpx，则为 httpx.Response 类型的实例。rpa 爬虫时，该字段为 None
        """
        self.url = url
        self.request = request
        self.headers = headers
        self._body_cache = body
        self.status = status
        self.encoding = request.encoding

        self._text_cache: str = text
        self._cookie_list_cache: list[dict[str, Any]] | None = cookie_list
        self._cookies_cache: dict[str, Any] | None = None
        self._selector: Selector | None = None

        self.driver = driver
        self.source_response = source_response

    def __str__(self):
        return f"<{self.status}> {self.url}"

    @property
    def body(self) -> bytes:
        if self._body_cache:
            return self._body_cache

        try:
            self._body_cache = self._text_cache.encode(self.encoding)
        except UnicodeEncodeError:
            try:
                _encoding = self._get_encoding()
                if _encoding:
                    self._body_cache = self._text_cache.encode(_encoding)
                else:
                    raise EncodeException(f"{self.request} {self.request.encoding} error.")
            except UnicodeEncodeError as e:
                raise EncodeException(e.encoding, e.object, e.start, e.end, f"{self.request}") from None
        return self._body_cache

    @property
    def text(self) -> str:
        if self._text_cache:
            return self._text_cache

        try:
            self._text_cache = self.body.decode(self.encoding)
        except UnicodeDecodeError:
            try:
                _encoding = self._get_encoding()
                if _encoding:
                    self._text_cache = self.body.decode(_encoding, errors="ignore")
                else:
                    raise DecodeException(f"{self.request} {self.request.encoding} error.")
            except UnicodeDecodeError as e:
                raise DecodeException(e.encoding, e.object, e.start, e.end, f"{self.request}") from None
        return self._text_cache

    def _get_encoding(self) -> str | None:
        _encoding_re = re.compile(r"charset=([\w-]+)", flags=re.I)

        _headers_encoding_string = self.headers.get("Content-Type", "") or self.headers.get("content-type", "")
        _encoding = _encoding_re.search(_headers_encoding_string)
        if _encoding:
            _encoding_str = _encoding.group(1)
            if (
                "text" not in _encoding_str
                and "html" not in _encoding_str
                and "gzip" not in _encoding_str
                and "/" not in _encoding_str
            ):
                return _encoding_str

        _encoding = _encoding_re.search(self.body.decode("utf-8", errors="ignore"))
        if _encoding:
            return _encoding.group(1)

        _body_encoding_re = re.compile(r'charset="([\w-]+)"', flags=re.I)
        _encoding = _body_encoding_re.search(self.body.decode("utf-8", errors="ignore"))
        if _encoding:
            return _encoding.group(1)
        return None

    @property
    def cookie_list(self) -> list[dict[str, str]]:
        if self._cookie_list_cache:
            return self._cookie_list_cache

        set_cookie_header = self.headers.get("Set-Cookie", "")

        cookie_obj = SimpleCookie()
        cookie_obj.load(set_cookie_header)

        self._cookie_list_cache = [
            {
                "name": name,
                "value": morsel.value,
                "domain": morsel.get("domain", ""),
                "path": morsel.get("path", ""),
                "expires": morsel.get("expires", ""),
                "secure": morsel.get("secure", ""),
                "httponly": morsel.get("httponly", ""),
            }
            for name, morsel in cookie_obj.items()
        ]

        return self._cookie_list_cache

    @property
    def cookies(self) -> dict[str, Any]:
        if self._cookies_cache:
            return self._cookies_cache

        self._cookies_cache = {cookie["key"]: cookie["value"] for cookie in self.cookie_list}
        return self._cookies_cache

    def json(self) -> dict[str, Any]:
        return ujson.loads(self.text)

    def urljoin(self, url: str) -> str:
        return _urljoin(self.url, url)

    def xpath(self, xpath: str) -> SelectorList[Selector]:
        if self._selector is None:
            self._selector = Selector(self.text)

        return self._selector.xpath(xpath)

    @property
    def meta(self) -> dict[str, Any]:
        return self.request.meta
