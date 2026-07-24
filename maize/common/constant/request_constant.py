"""
HTTP 请求常量。

定义 HTTP 方法枚举，供 :class:`~maize.common.http.request.Request` 使用。
"""

from enum import Enum, unique


@unique
class Method(Enum):
    """
    HTTP 方法枚举。
    """

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"
    PATCH = "PATCH"
