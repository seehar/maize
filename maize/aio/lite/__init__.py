"""
Lite 异步爬虫包。

轻量级异步爬虫实现，仅依赖 aiohttp，适合简单抓取场景。
"""

from maize.aio.lite.crawler import LiteCrawler
from maize.aio.lite.spider import LiteSpider

__all__ = ["LiteCrawler", "LiteSpider"]
