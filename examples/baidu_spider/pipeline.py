import typing

from maize import MysqlPipeline


if typing.TYPE_CHECKING:
    from maize import Item


class CustomPipeline(MysqlPipeline):
    async def process_error_item(self, items: list["Item"]):
        print("-" * 50)
        for item in items:
            print(item.__retry_count__, item)
        print("-" * 50)
