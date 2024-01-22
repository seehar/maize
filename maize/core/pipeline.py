import typing
from abc import ABCMeta


if typing.TYPE_CHECKING:
    from maize import Item


class BasePipeline(metaclass=ABCMeta):
    def __init__(self):
        pass

    async def handle_items(self, items: list["Item"]):
        pass
