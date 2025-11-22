from typing import Any


class InterceptRequest:
    def __init__(self, url: str, data: bytes | None, headers: dict[str, Any]):
        self.url = url
        self.data = data
        self.headers = headers


class InterceptResponse:
    def __init__(
        self,
        request: InterceptRequest,
        url: str,
        headers: dict[str, Any],
        content: bytes | None,
        status_code: int,
    ):
        self.request = request
        self.url = url
        self.headers = headers
        self.content = content
        self.status_code = status_code
