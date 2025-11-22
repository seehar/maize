from maize import Field, Item


class DemoItem(Item):
    __table_name__: str = "demo"
    age: int = Field(default=0)
    name: str = Field(default="notset")


class TestItem:
    def test_item_with_table_name(self):
        item = DemoItem()
        item.name = "bob"
        item.age = 10
        assert item.__table_name__ == "demo"

    def test_item_set_and_get(self):
        item = DemoItem()
        item.name = "bob"
        item.age = 10
        assert item.name == "bob"
        assert item.age == 10

    def test_item_set_and_get_1(self):
        item = DemoItem()
        item.name = "bob"
        item.age = 10
        assert item.name == "bob"
        assert item.age == 10

    def test_item_default_value(self):
        item = DemoItem()
        item.age = 10
        assert item.name == "notset"
        assert item.age == 10

    def test_item_update_table_name(self):
        item = DemoItem()
        item.name = "bob"
        item.age = 10
        item.__table_name__ = "demo2"
        assert item.__table_name__ == "demo2"
