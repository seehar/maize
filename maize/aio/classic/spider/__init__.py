"""
Classic 异步爬虫定义包。

导出 Spider 和 TaskSpider 基类，用户继承后实现抓取逻辑。
"""

from maize.aio.classic.spider.spider import Spider
from maize.aio.classic.spider.task_spider import TaskSpider

__all__ = ["Spider", "TaskSpider"]
