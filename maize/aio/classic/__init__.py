"""
Classic 异步爬虫包。

提供全功能的异步爬虫框架，包含 Spider、Crawler、CrawlerProcess 等核心组件。
"""

from maize.aio.classic.crawler.crawler import Crawler, CrawlerProcess
from maize.aio.classic.spider.spider import Spider
from maize.aio.classic.spider.task_spider import TaskSpider

__all__ = ["Crawler", "CrawlerProcess", "Spider", "TaskSpider"]
