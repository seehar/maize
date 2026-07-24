"""
异步 Classic 数据管道包，提供 Item 的持久化处理能力。

同步 Classic 的对应实现在 ``maize/sync/classic/pipeline/`` 下。
"""

from maize.pipelines.base_pipeline import BasePipeline
from maize.pipelines.empty_pipeline import EmptyPipeline
from maize.pipelines.mysql_pipeline import MysqlPipeline

__all__ = ["BasePipeline", "EmptyPipeline", "MysqlPipeline"]
