"""
数据管道包，提供 Item 的持久化处理能力。
"""

from maize.pipelines.base_pipeline import BasePipeline
from maize.pipelines.empty_pipeline import EmptyPipeline

__all__ = ["BasePipeline", "EmptyPipeline"]
