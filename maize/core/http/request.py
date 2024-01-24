import typing


class Request:
    def __init__(
        self,
        url: str,
        *,
        method: typing.Optional[str] = "GET",
        callback: typing.Optional[typing.Callable] = None,
        priority: int = 0,
        headers: typing.Optional[dict] = None,
        params: typing.Optional[dict] = None,
        data: typing.Optional[dict] = None,
        cookies: typing.Optional[dict] = None,
        proxy: typing.Optional[str] = None,
        proxy_username: typing.Optional[str] = None,
        proxy_password: typing.Optional[str] = None,
        encoding: typing.Optional[str] = "utf-8",
        meta: typing.Optional[dict] = None,
    ):
        """
        请求

        @param url: 待抓取的url
        @param method: 请求方式，如 GET, POST, PUT，默认 GET
        @param callback: 自定义的解析函数，默认为 parse
        @param priority: 请求优先级，默认为 0
        @param headers: 请求头
        @param params: 请求参数
        @param data: 请求 body
        @param cookies: 请求 cookies
        @param proxy: 代理ip
        @param proxy_username: 代理 ip 用户名
        @param proxy_password: 代理 ip 密码
        @param encoding: 编码，默认utf-8，当无法解析时，使用响应中的编码
        @param meta: 自定义数据
        """
        self.url = url
        self.method = method.upper()
        self.callback = callback
        self.priority = priority
        self.headers = headers
        self.params = params
        self.data = data
        self.cookies = cookies
        self.proxy = proxy
        self.proxy_username = proxy_username
        self.proxy_password = proxy_password

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
