"""
同步 Classic 爬虫完整栈，包含引擎、调度器、中间件、管道、处理器等组件。
"""

from maize.sync.classic.crawler import SyncCrawler, SyncCrawlerProcess
from maize.sync.classic.downloader import SyncBaseDownloader, SyncHttpxDownloader, SyncRequestsDownloader
from maize.sync.classic.middleware import (
    SyncBaseMiddleware,
    SyncDownloaderMiddleware,
    SyncDownloaderMiddlewareManager,
    SyncMiddlewareManager,
    SyncPipelineMiddleware,
    SyncPipelineMiddlewareManager,
    SyncSpiderMiddleware,
    SyncSpiderMiddlewareManager,
)
from maize.sync.classic.pipeline import SyncBasePipeline, SyncEmptyPipeline, SyncPipelineScheduler
from maize.sync.classic.processor import SyncProcessor
from maize.sync.classic.scheduler import SyncSpiderPriorityQueue
from maize.sync.classic.spider import SyncSpider, SyncTaskSpider

__all__ = [
    "SyncBaseDownloader",
    "SyncBaseMiddleware",
    "SyncBasePipeline",
    "SyncCrawler",
    "SyncCrawlerProcess",
    "SyncDownloaderMiddleware",
    "SyncDownloaderMiddlewareManager",
    "SyncEmptyPipeline",
    "SyncHttpxDownloader",
    "SyncMiddlewareManager",
    "SyncPipelineMiddleware",
    "SyncPipelineMiddlewareManager",
    "SyncPipelineScheduler",
    "SyncProcessor",
    "SyncRequestsDownloader",
    "SyncSpider",
    "SyncSpiderMiddleware",
    "SyncSpiderMiddlewareManager",
    "SyncSpiderPriorityQueue",
    "SyncTaskSpider",
]
