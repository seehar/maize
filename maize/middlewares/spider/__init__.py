"""
Built-in spider middlewares for Maize framework.
"""

from maize.middlewares.spider.depth_middleware import DepthMiddleware
from maize.middlewares.spider.http_error_middleware import HttpErrorMiddleware

__all__ = [
    "DepthMiddleware",
    "HttpErrorMiddleware",
]
