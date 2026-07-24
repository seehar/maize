"""
Classic 异步数据管道包。

导出 BasePipeline 和 EmptyPipeline，用于 Item 的后处理与持久化。
"""

from maize.pipelines import BasePipeline, EmptyPipeline

__all__ = ["BasePipeline", "EmptyPipeline"]
