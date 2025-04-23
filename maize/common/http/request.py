import hashlib
import typing

from maize.common.constant.request_constant import Method


class Request:
    def __init__(
        self,
        url: str,
        *,
        method: typing.Optional[Method] = Method.GET,
        callback: typing.Optional[typing.Callable] = None,
        priority: int = 0,
        headers: typing.Optional[dict] = None,
        headers_func: typing.Optional[typing.Callable[[], typing.Awaitable[dict]]] = None,
        params: typing.Optional[dict] = None,
        data: typing.Optional[dict | str] = None,
        json: typing.Optional[dict] = None,
        cookies: typing.Optional[dict | list[dict[str, typing.Any]]] = None,
        proxy: typing.Optional[str] = None,
        proxy_username: typing.Optional[str] = None,
        proxy_password: typing.Optional[str] = None,
        encoding: typing.Optional[str] = "utf-8",
        meta: typing.Optional[dict] = None,
        follow_redirects: bool = True,
        max_redirects: int = 20,
    ):
        """
        请求

        :param url: 待抓取的url
        :param method: 请求方式，如 Method.GET, Method.POST, Method.PUT，默认 Method.GET
        :param callback: 自定义的解析函数，默认为 parse
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
        return self._meta

    @property
    def current_retry_count(self):
        return self._current_retry_count

    def retry(self):
        self._current_retry_count += 1

    @property
    def hash(self) -> str:
        request_data_list = [
            self.method,
            self.url,
            self.headers or "",
            self.params or "",
            self.data or "",
        ]
        request_data_str = ":".join(request_data_list)
        return hashlib.md5(request_data_str.encode("utf-8")).hexdigest()

    @property
    def model_dump(self):
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
        return await self.headers_func() if self.headers_func else self.headers
