import typing
from abc import ABCMeta


if typing.TYPE_CHECKING:
    from maize import Item
    from maize.core.settings.settings_manager import SettingsManager


class BasePipeline(metaclass=ABCMeta):
    def __init__(self, settings: "SettingsManager"):
        self.settings = settings

    async def open(self):
        pass

    async def close(self):
        pass

    async def process_item(self, items: list["Item"]):
        pass
