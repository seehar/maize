"""同步空管道。"""

from typing import TYPE_CHECKING

from maize.sync.classic.pipeline.sync_base_pipeline import SyncBasePipeline

if TYPE_CHECKING:
    from maize.common.items import Item


class SyncEmptyPipeline(SyncBasePipeline):
    """同步空管道，不做任何操作。"""

    def open(self):
        pass

    def close(self):
        pass

    def process_item(self, items: list["Item"]) -> bool:
        return True

    def process_error_item(self, items: list["Item"]):
        pass
