"""
空管道实现。

作为默认管道使用，不执行任何数据处理操作，所有方法为空实现。
"""

from typing import TYPE_CHECKING

from maize.pipelines.base_pipeline import BasePipeline

if TYPE_CHECKING:
    from maize import Item


class EmptyPipeline(BasePipeline):
    """
    空管道，不执行任何数据处理，用作默认占位管道。
    """

    async def open(self):
        """
        管道初始化，空实现无需操作。
        """
        pass

    async def close(self):
        """
        管道关闭，空实现无需操作。
        """
        pass

    async def process_item(self, items: list["Item"]) -> bool:
        """
        处理数据项，空实现直接返回成功。

        :param items: 待处理的 Item 列表
        :return: 始终返回 True
        """
        return True

    async def process_error_item(self, items: list["Item"]):
        """
        处理错误数据项，空实现无需操作。

        :param items: 超过重试次数的 Item 列表
        """
        pass
