"""
Classic 异步请求调度器。

直接使用 ``SpiderPriorityQueue``，无额外包装层。
"""

from maize.utils.priority_queue import SpiderPriorityQueue

__all__ = ["SpiderPriorityQueue"]
