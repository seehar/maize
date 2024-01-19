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
        body: typing.Optional[bytes] = None,
        proxies: typing.Optional[dict] = None,
        encoding: typing.Optional[str] = "utf-8",
        meta: typing.Optional[dict] = None,
    ):
        self.url = url
        self.method = method.upper()
        self.callback = callback
        self.priority = priority
        self.headers = headers
        self.params = params
        self.data = data
        self.cookies = cookies
        self.body = body
        self.proxies = proxies

        self.encoding = encoding
        self._meta = meta if meta is not None else {}

    def __str__(self):
        return f"{self.method} {self.url}"

    def __lt__(self, other):
        return self.priority < other.priority

    @property
    def meta(self) -> dict:
        return self._meta
