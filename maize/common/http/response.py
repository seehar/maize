"""
HTTP 响应模型。

定义 :class:`Response`，封装下载器返回的响应数据，
提供 body/text 编解码、Cookie 解析、JSON 解析和 XPath 选择器等功能。
"""

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
    """
    HTTP 响应对象。

    封装下载器返回的响应数据，支持 body/text 自动编解码（含编码探测）、
    Cookie 解析、JSON 反序列化和 XPath 选择器。

    :param url: 响应 URL
    :param headers: 响应头字典
    :param request: 对应的请求对象
    :param body: 响应体字节，默认空
    :param text: 响应体文本，默认空
    :param status: HTTP 状态码，默认 200
    :param cookie_list: Cookie 列表，默认 None
    :param driver: 浏览器驱动实例（RPA 下载器使用），默认 None
    :param source_response: 下载器原始响应对象（如 httpx.Response），默认 None
    """

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
        """
        响应体字节。

        优先返回缓存；若无缓存则尝试用请求编码将 text 编码为 bytes，
        编码失败时自动探测响应中的 charset。

        :return: 响应体字节
        :raises EncodeException: 编码失败且无法探测到可用编码时抛出
        """

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
        """
        响应体文本。

        优先返回缓存；若无缓存则尝试用请求编码将 body 解码为 str，
        解码失败时自动探测响应中的 charset。

        :return: 响应体文本
        :raises DecodeException: 解码失败且无法探测到可用编码时抛出
        """

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
        """
        从响应头和响应体中探测字符编码。

        依次尝试：Content-Type 头中的 charset、响应体文本中的 charset 声明、
        带引号的 charset 声明。

        :return: 探测到的编码字符串，未找到时返回 None
        """

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

        _search_text = self._text_cache or self._body_cache.decode("utf-8", errors="ignore")

        _encoding = _encoding_re.search(_search_text)
        if _encoding:
            return _encoding.group(1)

        _body_encoding_re = re.compile(r'charset="([\w-]+)"', flags=re.I)
        _encoding = _body_encoding_re.search(_search_text)
        if _encoding:
            return _encoding.group(1)
        return None

    @property
    def cookie_list(self) -> list[dict[str, str]]:
        """
        解析 Set-Cookie 头为 Cookie 字典列表。

        每个字典包含 name、value、domain、path、expires、secure、httponly 字段。
        结果会被缓存。

        :return: Cookie 字典列表
        """

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
        """
        以键值对形式返回所有 Cookie。

        基于 :attr:`cookie_list` 构建，结果会被缓存。

        :return: Cookie 键值对字典
        """

        if self._cookies_cache:
            return self._cookies_cache

        self._cookies_cache = {cookie["key"]: cookie["value"] for cookie in self.cookie_list}
        return self._cookies_cache

    def json(self) -> dict[str, Any]:
        """
        将响应体解析为 JSON 字典。

        :return: 解析后的字典
        :raises ValueError: 响应体不是合法 JSON 时抛出
        """

        return ujson.loads(self.text)

    def urljoin(self, url: str) -> str:
        """
        将相对 URL 拼接为绝对 URL。

        :param url: 相对或绝对 URL
        :return: 拼接后的绝对 URL
        """

        return _urljoin(self.url, url)

    def xpath(self, xpath: str) -> SelectorList[Selector]:
        """
        使用 XPath 表达式查询响应内容。

        首次调用时自动构建 Selector 并缓存。

        :param xpath: XPath 表达式
        :return: 匹配结果列表
        """

        if self._selector is None:
            self._selector = Selector(self.text)

        return self._selector.xpath(xpath)

    @property
    def meta(self) -> dict[str, Any]:
        """
        对应请求的自定义元数据字典。
        """

        return self.request.meta
