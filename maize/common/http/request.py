"""
HTTP 请求模型。

定义 :class:`Request`，封装爬虫发起 HTTP 请求所需的全部参数，
并支持优先级比较、去重哈希、重试计数和请求头异步/同步获取。
"""

import hashlib
import inspect
import typing

from maize.common.constant.request_constant import Method


class Request:
    """
    HTTP 请求对象。

    封装一次 HTTP 请求的 URL、方法、回调、请求头、代理等全部参数，
    支持优先级排序（数值越小越优先）、基于 MD5 的去重哈希和重试计数。
    """

    def __init__(
        self,
        url: str,
        *,
        method: Method | None = Method.GET,
        callback: typing.Callable | None = None,
        error_callback: typing.Callable | None = None,
        priority: int = 0,
        headers: dict | None = None,
        headers_func: typing.Callable[[], typing.Awaitable[dict]] | None = None,
        params: dict | None = None,
        data: dict | str | None = None,
        json: dict | None = None,
        cookies: dict | list[dict[str, typing.Any]] | None = None,
        proxy: str | None = None,
        proxy_username: str | None = None,
        proxy_password: str | None = None,
        encoding: str | None = "utf-8",
        meta: dict | None = None,
        follow_redirects: bool = True,
        max_redirects: int = 20,
    ):
        """
        请求

        :param url: 待抓取的url
        :param method: 请求方式，如 Method.GET, Method.POST, Method.PUT，默认 Method.GET
        :param callback: 自定义的解析函数，默认为 parse
        :param error_callback: 自定义的错误回调函数
        :param priority: 请求优先级，默认为 0
        :param headers: 请求头
        :param params: 请求参数
        :param data: 请求 body
        :param json: dict 类型的参数
        :param cookies: 请求 cookies
        :param proxy: 代理ip
        :param proxy_username: 代理 ip 用户名
        :param proxy_password: 代理 ip 密码
        :param encoding: 编码，默认utf-8，当无法解析时，使用响应中的编码
        :param meta: 自定义数据
        :param follow_redirects: 是否允许重定向
        :param max_redirects: 最大重定向次数，默认为 20
        """
        self.url = url
        self.method: str = str(method.value)
        self.callback = callback
        self.error_callback = error_callback
        self.priority = priority
        self.headers = headers
        self.headers_func = headers_func
        self.params = params
        self.data = data
        self.json = json
        self.cookies = cookies
        self.proxy = proxy
        self.proxy_username = proxy_username
        self.proxy_password = proxy_password

        self.follow_redirects = follow_redirects
        self.max_redirects = max_redirects

        # 当前重试次数
        self._current_retry_count: int = 0

        self.encoding = encoding
        self._meta = meta if meta is not None else {}

    def __str__(self):
        return f"{self.method} {self.url}"

    def __lt__(self, other):
        return self.priority < other.priority

    @property
    def meta(self) -> dict:
        """
        请求附带的自定义元数据字典。
        """

        return self._meta

    @property
    def current_retry_count(self):
        """
        当前已重试次数。
        """

        return self._current_retry_count

    def retry(self):
        """
        将重试计数加一。
        """

        self._current_retry_count += 1

    @property
    def hash(self) -> str:
        """
        基于 method、url、headers、params、data、json 计算的 MD5 去重哈希。
        """

        request_data_list = [
            self.method,
            self.url,
            repr(self.headers) or "",
            repr(self.params) or "",
            repr(self.data) or "",
            repr(self.json) or "",
        ]
        request_data_str = ":".join(request_data_list)
        return hashlib.md5(request_data_str.encode("utf-8")).hexdigest()

    @property
    def model_dump(self):
        """
        将请求的关键字段序列化为字典，用于日志记录和调试。
        """

        return {
            "url": self.url,
            "method": self.method,
            "callback": self.callback.__name__ if self.callback else None,
            "priority": self.priority,
            "headers": self.headers,
            "params": self.params,
            "data": self.data,
            "cookies": self.cookies,
            "proxy": self.proxy,
            "proxy_username": self.proxy_username,
            "proxy_password": self.proxy_password,
        }

    async def get_headers(self) -> dict:
        """
        异步获取请求头。

        若设置了 ``headers_func``，则调用该异步函数获取请求头；
        否则返回构造时传入的静态 ``headers``。

        :return: 请求头字典
        """

        return await self.headers_func() if self.headers_func else self.headers

    def get_headers_sync(self) -> dict:
        """
        同步获取请求头，用于同步爬虫。

        若 ``headers_func`` 返回协程则抛出 TypeError，
        同步爬虫必须使用同步可调用对象。

        :return: 请求头字典
        :raises TypeError: headers_func 返回协程时抛出
        """
        if self.headers_func:
            result = self.headers_func()
            if inspect.iscoroutine(result):
                result.close()
                raise TypeError(
                    "headers_func returned a coroutine; sync spiders require a sync callable. "
                    "Use a plain function returning dict, not an async function."
                )
            return result
        return self.headers
