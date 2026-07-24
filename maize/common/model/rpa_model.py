"""
RPA 网络拦截数据模型。

定义浏览器请求/响应拦截时使用的数据结构，
供 Playwright / Patchright 下载器的资源拦截功能使用。
"""

from typing import Any


class InterceptRequest:
    """
    被拦截的浏览器请求，记录 URL、请求体和请求头。
    """

    def __init__(self, url: str, data: bytes | None, headers: dict[str, Any]):
        """
        初始化拦截请求。

        :param url: 请求 URL
        :param data: 请求体字节，无请求体时为 None
        :param headers: 请求头字典
        """

        self.url = url
        self.data = data
        self.headers = headers


class InterceptResponse:
    """
    被拦截的浏览器响应，记录请求、URL、响应头、响应体和状态码。
    """

    def __init__(
        self,
        request: InterceptRequest,
        url: str,
        headers: dict[str, Any],
        content: bytes | None,
        status_code: int,
    ):
        """
        初始化拦截响应。

        :param request: 对应的拦截请求
        :param url: 响应 URL
        :param headers: 响应头字典
        :param content: 响应体字节，无内容时为 None
        :param status_code: HTTP 状态码
        """

        self.request = request
        self.url = url
        self.headers = headers
        self.content = content
        self.status_code = status_code
