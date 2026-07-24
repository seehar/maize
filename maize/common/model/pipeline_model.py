"""
管道处理结果模型。

记录管道批量处理的成功/失败计数，支持结果累加。
"""

from maize.common.model.base_model import BaseModel


class PipelineProcessResult(BaseModel):
    """
    管道处理结果，记录成功和失败的条目数。

    :ivar success_count: 处理成功的条目数，默认 0
    :ivar fail_count: 处理失败的条目数，默认 0
    """

    success_count: int = 0
    fail_count: int = 0

    def add(self, result: "PipelineProcessResult"):
        """
        累加另一个处理结果到当前实例。

        :param result: 待累加的处理结果
        """

        self.success_count += result.success_count
        self.fail_count += result.fail_count
