"""
Tests for ItemCleanerMiddleware _clean_value and process_item_before.
"""

import pytest

from maize.common.items import Item
from maize.common.items.field import Field
from maize.middlewares.pipeline.cleaner import ItemCleanerMiddleware


class CleanItem(Item):
    __table_name__: str = "clean"
    title: str = ""
    description: str = ""
    count: int = 0
    tags: list = Field(default_factory=list)


class TestCleanValue:
    """Test ItemCleanerMiddleware._clean_value."""

    def _make_middleware(self, **kwargs):
        return ItemCleanerMiddleware(**kwargs)

    def test_strips_whitespace(self):
        mw = self._make_middleware()
        assert mw._clean_value("  hello  ") == "hello"

    def test_normalizes_whitespace(self):
        mw = self._make_middleware()
        assert mw._clean_value("hello    world") == "hello world"

    def test_remove_html(self):
        mw = self._make_middleware(remove_html=True)
        assert mw._clean_value("<b>hello</b>") == "hello"

    def test_remove_html_disabled(self):
        mw = self._make_middleware(remove_html=False)
        assert mw._clean_value("<b>hello</b>") == "<b>hello</b>"

    def test_empty_to_none(self):
        mw = self._make_middleware(empty_to_none=True)
        assert mw._clean_value("") is None

    def test_empty_to_none_disabled(self):
        mw = self._make_middleware(empty_to_none=False)
        assert mw._clean_value("") == ""

    def test_non_string_returned_as_is(self):
        mw = self._make_middleware()
        assert mw._clean_value(42) == 42
        assert mw._clean_value(None) is None
        assert mw._clean_value(True) is True

    def test_all_options_combined(self):
        mw = self._make_middleware(
            strip_whitespace=True, remove_html=True, normalize_whitespace=True, empty_to_none=True
        )
        assert mw._clean_value("  <b>  hello   world  </b>  ") == "hello world"

    def test_strips_and_normalizes_whitespace(self):
        mw = self._make_middleware()
        assert mw._clean_value("\thello\n\tworld  ") == "hello world"


class TestProcessItemBefore:
    """Test ItemCleanerMiddleware.process_item_before."""

    @pytest.mark.asyncio
    async def test_cleans_string_fields(self):
        mw = ItemCleanerMiddleware()
        item = CleanItem(title="  hello  ", description="  world  ")
        spider = MagicMock()
        result = await mw.process_item_before(item, spider)
        assert result.title == "hello"
        assert result.description == "world"

    @pytest.mark.asyncio
    async def test_cleans_list_fields(self):
        mw = ItemCleanerMiddleware()
        item = CleanItem(tags=["  a  ", "  b  "])
        spider = MagicMock()
        await mw.process_item_before(item, spider)
        assert item.tags == ["a", "b"]

    @pytest.mark.asyncio
    async def test_excluded_fields_not_cleaned(self):
        mw = ItemCleanerMiddleware(excluded_fields=["title"])
        item = CleanItem(title="  not cleaned  ", description="  cleaned  ")
        spider = MagicMock()
        await mw.process_item_before(item, spider)
        assert item.title == "  not cleaned  "
        assert item.description == "cleaned"

    @pytest.mark.asyncio
    async def test_non_string_fields_unchanged(self):
        mw = ItemCleanerMiddleware()
        item = CleanItem(count=42)
        spider = MagicMock()
        await mw.process_item_before(item, spider)
        assert item.count == 42

    @pytest.mark.asyncio
    async def test_remove_html_in_process_item(self):
        mw = ItemCleanerMiddleware(remove_html=True)
        item = CleanItem(title="<b>hello</b>")
        spider = MagicMock()
        await mw.process_item_before(item, spider)
        assert item.title == "hello"

    @pytest.mark.asyncio
    async def test_from_crawler(self):
        crawler = MagicMock()
        crawler.settings = MagicMock()
        mw = ItemCleanerMiddleware.from_crawler(crawler)
        assert isinstance(mw, ItemCleanerMiddleware)


# Minimal import for type hint
from unittest.mock import MagicMock  # noqa: E402
