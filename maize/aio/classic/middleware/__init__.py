"""
Classic 异步中间件包。

重导出所有可用的中间件组件，供引擎在请求/响应/Spider 三层调用。
"""

from maize.middlewares import (
    DefaultHeadersMiddleware,
    DepthMiddleware,
    DownloaderMiddleware,
    HttpErrorMiddleware,
    ItemCleanerMiddleware,
    ItemValidationMiddleware,
    PipelineMiddleware,
    RetryMiddleware,
    SpiderMiddleware,
    UserAgentMiddleware,
)

__all__ = [
    "DefaultHeadersMiddleware",
    "DepthMiddleware",
    "DownloaderMiddleware",
    "HttpErrorMiddleware",
    "ItemCleanerMiddleware",
    "ItemValidationMiddleware",
    "PipelineMiddleware",
    "RetryMiddleware",
    "SpiderMiddleware",
    "UserAgentMiddleware",
]
