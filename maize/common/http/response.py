import re
from http.cookies import SimpleCookie
from typing import TYPE_CHECKING
from typing import Any
from typing import Dict
from typing import Generic
from typing import List
from typing import Optional
from typing import TypeVar
from typing import Union
from urllib.parse import urljoin as _urljoin

import ujson
from parsel import Selector
from parsel import SelectorList

from maize.exceptions.spider_exception import DecodeException
from maize.exceptions.spider_exception import EncodeException


if TYPE_CHECKING:
    from maize.common.http.request import Request

Driver = TypeVar("Driver")
R = TypeVar("R")


class Response(Generic[Driver, R]):
    def __init__(
        self,
        url: str,
        *,
        headers: Dict[str, Any],
        request: "Request",
        body: bytes = b"",
        text: str = "",
        status: int = 200,
        cookie_list: Optional[List[Dict[str, Union[str, bool]]]] = None,
        driver: Optional[Driver] = None,
        source_response: Optional[R] = None,
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
        self._cookie_list_cache: Optional[List[Dict[str, Any]]] = cookie_list
        self._cookies_cache: Optional[Dict[str, Any]] = None
        self._selector: Optional[Selector] = None

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
                raise EncodeException(e.encoding, e.object, e.start, e.end, f"{self.request}")
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
                    self._text_cache = self.body.decode(_encoding)
                else:
                    raise DecodeException(f"{self.request} {self.request.encoding} error.")
            except UnicodeDecodeError as e:
                raise DecodeException(e.encoding, e.object, e.start, e.end, f"{self.request}")
        return self._text_cache

    def _get_encoding(self) -> Optional[str]:
        _encoding_re = re.compile(r"charset=([\w-]+)", flags=re.I)
        _encoding_string = self.headers.get("Content-Type", "") or self.headers.get("content-type", "")
        _encoding = _encoding_re.search(_encoding_string)
        return _encoding.group(1) if _encoding else None

    @property
    def cookie_list(self) -> List[Dict[str, str]]:
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
    def cookies(self) -> Dict[str, Any]:
        if self._cookies_cache:
            return self._cookies_cache

        self._cookies_cache = {cookie["key"]: cookie["value"] for cookie in self.cookie_list}
        return self._cookies_cache

    def json(self) -> Dict[str, Any]:
        return ujson.loads(self.text)

    def urljoin(self, url: str) -> str:
        return _urljoin(self.url, url)

    def xpath(self, xpath: str) -> SelectorList[Selector]:
        if self._selector is None:
            self._selector = Selector(self.text)

        return self._selector.xpath(xpath)

    @property
    def meta(self) -> Dict[str, Any]:
        return self.request.meta
