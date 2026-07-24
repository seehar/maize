"""
异步 Classic 中间件系统。

本包为异步 Classic 爬虫专属。同步 Classic 的对应实现在
``maize/sync/classic/middleware/`` 下。两套中间件接口不共享——
异步中间件方法为 ``async def``，同步中间件为普通方法。

中间件类型：
    - DownloaderMiddleware: 请求前/响应后处理
    - SpiderMiddleware: 爬虫输入/输出处理
    - PipelineMiddleware: Item 管道前/后处理
"""

from maize.middlewares.base_middleware import (
    BaseMiddleware,
    DownloaderMiddleware,
    PipelineMiddleware,
    SpiderMiddleware,
)

# Import built-in middleware
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
