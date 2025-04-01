from typing import Any
from typing import Dict
from typing import Optional


class InterceptRequest:
    def __init__(self, url: str, data: Optional[bytes], headers: Dict[str, Any]):
        self.url = url
        self.data = data
        self.headers = headers


class InterceptResponse:
    def __init__(
        self,
        request: InterceptRequest,
        url: str,
        headers: Dict[str, Any],
        content: Optional[bytes],
        status_code: int,
    ):
        self.request = request
        self.url = url
        self.headers = headers
        self.content = content
        self.status_code = status_code
