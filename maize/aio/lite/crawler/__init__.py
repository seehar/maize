"""
Lite 爬虫运行器包。

导出 LiteCrawler，负责 Lite 爬虫的并发调度与生命周期管理。
"""

from maize.aio.lite.crawler.lite_crawler import LiteCrawler

__all__ = ["LiteCrawler"]
