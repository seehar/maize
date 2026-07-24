"""
同步 Lite 轻量级爬虫，httpx + 线程池，无中间件/管道依赖。
"""

from maize.sync.lite.crawler import SyncLiteCrawler
from maize.sync.lite.spider import SyncLiteSpider

__all__ = ["SyncLiteCrawler", "SyncLiteSpider"]
