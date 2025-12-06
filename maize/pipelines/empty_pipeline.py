from typing import TYPE_CHECKING

from maize.pipelines.base_pipeline import BasePipeline

if TYPE_CHECKING:
    from maize import Item


class EmptyPipeline(BasePipeline):
    async def open(self):
        pass

    async def close(self):
        pass

    async def process_item(self, items: list["Item"]) -> bool:
        return True

    async def process_error_item(self, items: list["Item"]):
        pass
