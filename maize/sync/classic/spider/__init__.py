"""
同步 Spider 基类和任务 Spider。
"""

from maize.sync.classic.spider.sync_spider import SyncSpider
from maize.sync.classic.spider.sync_task_spider import SyncTaskSpider

__all__ = ["SyncSpider", "SyncTaskSpider"]
