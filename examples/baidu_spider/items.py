from maize import Field
from maize import Item


class BaiduItem(Item):
    __table_name__ = "baidu_spider"
    url = Field()
    title = Field()
