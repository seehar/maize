from typing import TYPE_CHECKING
from typing import List

from maize import MysqlPipeline


if TYPE_CHECKING:
    from maize import Item


class CustomPipeline(MysqlPipeline):
    async def process_error_item(self, items: List["Item"]):
        print("-" * 50)
        for item in items:
            print(item.__retry_count__, item)
        print("-" * 50)
