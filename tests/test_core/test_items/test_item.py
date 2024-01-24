import pytest

from maize import Field
from maize import Item


class DemoItem(Item):
    __table_name__ = "demo"
    age = Field()
    name = Field()


class TestItem:
    def test_item_with_table_name(self):
        item = DemoItem()
        item["name"] = "bob"
        item["age"] = 10
        assert item.__table_name__ == "demo"

    def test_item_update_table_name_key_error(self):
        item = DemoItem()
        item["name"] = "bob"
        item["age"] = 10
        with pytest.raises(KeyError):
            item["__table_name__"] = "demo2"

    def test_item_update_table_name(self):
        item = DemoItem()
        item["name"] = "bob"
        item["age"] = 10
        item.__table_name__ = "demo2"
        assert item.__table_name__ == "demo2"
