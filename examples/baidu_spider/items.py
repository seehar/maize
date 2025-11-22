from maize import Field, Item


class BaiduItem(Item):
    __table_name__ = "baidu_spider"
    url: str | None = Field(default=None)
    title: str | None = Field(default=None)
