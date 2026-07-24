"""同步空管道。"""

from typing import TYPE_CHECKING

from maize.sync.classic.pipeline.sync_base_pipeline import SyncBasePipeline

if TYPE_CHECKING:
    from maize.common.items import Item


class SyncEmptyPipeline(SyncBasePipeline):
    """同步空管道，不做任何操作。"""

    def open(self):
        """
        打开管道（空操作）。
        """
        pass

    def close(self):
        """
        关闭管道（空操作）。
        """
        pass

    def process_item(self, items: list["Item"]) -> bool:
        """
        处理 Item（空操作，直接返回成功）。

        :param items: 批量 Item
        :return: 始终返回 True
        """
        return True

    def process_error_item(self, items: list["Item"]):
        """
        处理错误 Item（空操作）。

        :param items: 批量错误 Item
        """
        pass
