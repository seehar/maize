"""
同步中间件基类和管理器，覆盖下载器、Spider、管道三层中间件。
"""

from maize.sync.classic.middleware.sync_base_middleware import (
    SyncBaseMiddleware,
    SyncDownloaderMiddleware,
    SyncPipelineMiddleware,
    SyncSpiderMiddleware,
)
from maize.sync.classic.middleware.sync_middleware_manager import (
    SyncDownloaderMiddlewareManager,
    SyncMiddlewareManager,
    SyncPipelineMiddlewareManager,
    SyncSpiderMiddlewareManager,
)

__all__ = [
    "SyncBaseMiddleware",
    "SyncDownloaderMiddleware",
    "SyncDownloaderMiddlewareManager",
    "SyncMiddlewareManager",
    "SyncPipelineMiddleware",
    "SyncPipelineMiddlewareManager",
    "SyncSpiderMiddleware",
    "SyncSpiderMiddlewareManager",
]
