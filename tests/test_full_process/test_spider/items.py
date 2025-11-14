from maize import Field
from maize import Item


class BaiduItem(Item):
    url: str = Field()
    title: str = Field()
