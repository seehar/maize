"""
Built-in downloader middlewares for Maize framework.
"""

from maize.middlewares.downloader.default_headers_middleware import DefaultHeadersMiddleware
from maize.middlewares.downloader.retry_middleware import RetryMiddleware
from maize.middlewares.downloader.user_agent_middleware import UserAgentMiddleware

__all__ = [
    "DefaultHeadersMiddleware",
    "RetryMiddleware",
    "UserAgentMiddleware",
]
