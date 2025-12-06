"""
Maize Middleware System

This package provides a flexible middleware system for the Maize web scraping framework.
Middlewares can process requests, responses, spider callbacks, and items at various
stages of the scraping pipeline.

Middleware Types:
    - DownloaderMiddleware: Process requests before downloading and responses after
    - SpiderMiddleware: Process spider input/output and start requests
    - PipelineMiddleware: Process items before/after pipeline processing

Example:
    >>> from maize.middlewares import DownloaderMiddleware
    >>>
    >>> class MyMiddleware(DownloaderMiddleware):
    ...     async def process_request(self, request, spider):
    ...         # Modify request before downloading
    ...         request.headers['User-Agent'] = 'MyBot/1.0'
    ...         return request
"""

from maize.middlewares.base_middleware import (
    BaseMiddleware,
    DownloaderMiddleware,
    PipelineMiddleware,
    SpiderMiddleware,
)

# Import built-in middlewares
from maize.middlewares.downloader import (
    DefaultHeadersMiddleware,
    RetryMiddleware,
    UserAgentMiddleware,
)
from maize.middlewares.middleware_manager import (
    DownloaderMiddlewareManager,
    MiddlewareManager,
    PipelineMiddlewareManager,
    SpiderMiddlewareManager,
)
from maize.middlewares.pipeline import (
    ItemCleanerMiddleware,
    ItemValidationMiddleware,
)
from maize.middlewares.spider import (
    DepthMiddleware,
    HttpErrorMiddleware,
)

__all__ = [
    # Base classes
    "BaseMiddleware",
    "DefaultHeadersMiddleware",
    "DepthMiddleware",
    "DownloaderMiddleware",
    "DownloaderMiddlewareManager",
    "HttpErrorMiddleware",
    "ItemCleanerMiddleware",
    "ItemValidationMiddleware",
    "MiddlewareManager",
    "PipelineMiddleware",
    "PipelineMiddlewareManager",
    "RetryMiddleware",
    "SpiderMiddleware",
    "SpiderMiddlewareManager",
    "UserAgentMiddleware",
]
