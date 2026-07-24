"""
Classic 异步调度器包。

导出 Scheduler，负责请求的优先级排队与出队调度。
"""

from maize.aio.classic.scheduler.scheduler import Scheduler

__all__ = ["Scheduler"]
