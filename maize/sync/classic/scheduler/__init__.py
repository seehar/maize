"""
同步请求调度器。

直接使用 ``SyncSpiderPriorityQueue``，无额外包装层。
"""

from maize.utils.sync_priority_queue import SyncSpiderPriorityQueue

__all__ = ["SyncSpiderPriorityQueue"]
