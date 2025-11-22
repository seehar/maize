from maize import Field, Item


class BaiduItem(Item):
    url: str | None = Field(default=None)
    title: str | None = Field(default=None)
