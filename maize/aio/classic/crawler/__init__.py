"""
Classic 异步爬虫运行器包。

导出 Crawler 和 CrawlerProcess，负责爬虫实例的创建与调度。
"""

from maize.aio.classic.crawler.crawler import Crawler, CrawlerProcess

__all__ = ["Crawler", "CrawlerProcess"]
