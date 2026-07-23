"""Tests for StringUtil."""

import pytest

from maize.utils.string_util import StringUtil


class TestStringUtil:
    """Test camel_to_snake conversion."""

    @pytest.mark.parametrize(
        ("camel", "expected"),
        [
            ("camelCase", "camel_case"),
            ("PascalCase", "pascal_case"),
            ("simple", "simple"),
            ("HTTPResponse", "httpresponse"),
            ("getUserID", "get_user_id"),
            ("XMLParser", "xmlparser"),
            ("a", "a"),
            ("A", "a"),
            ("abc123Def", "abc123_def"),
            ("already_snake", "already_snake"),
            ("withNumbers123", "with_numbers123"),
            ("ABCDef", "abcdef"),
        ],
    )
    def test_camel_to_snake(self, camel: str, expected: str):
        assert StringUtil.camel_to_snake(camel) == expected

    def test_camel_to_snake_empty_string(self):
        assert StringUtil.camel_to_snake("") == ""

    def test_camel_to_snake_all_uppercase(self):
        assert StringUtil.camel_to_snake("URL") == "url"

    def test_camel_to_snake_single_char_upper(self):
        assert StringUtil.camel_to_snake("A") == "a"

    def test_camel_to_snake_digit_transition(self):
        """Digit followed by uppercase should insert underscore."""
        assert StringUtil.camel_to_snake("version2Update") == "version2_update"
