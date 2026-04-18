"""
Tests for cookie_util
"""

from maize.utils.cookie_util import CookieUtil


class TestCookieUtil:
    """Test CookieUtil"""

    def test_str_cookies_to_list_empty(self):
        """Test with empty cookie string"""
        result = CookieUtil.str_cookies_to_list("", "example.com")
        assert result == []

    def test_str_cookies_to_list_none(self):
        """Test with None cookie string"""
        result = CookieUtil.str_cookies_to_list(None, "example.com")
        assert result == []

    def test_str_cookies_to_list_single(self):
        """Test with single cookie"""
        result = CookieUtil.str_cookies_to_list("foo=bar", "example.com")

        assert len(result) == 1
        assert result[0]["name"] == "foo"
        assert result[0]["value"] == "bar"
        assert result[0]["domain"] == "example.com"

    def test_str_cookies_to_list_multiple(self):
        """Test with multiple cookies"""
        result = CookieUtil.str_cookies_to_list("foo=bar; baz=qux", "example.com")

        assert len(result) == 2
        assert result[0]["name"] == "foo"
        assert result[0]["value"] == "bar"
        assert result[1]["name"] == "baz"
        assert result[1]["value"] == "qux"

    def test_str_cookies_to_list_with_equals_in_value(self):
        """Test cookie value containing equals sign"""
        result = CookieUtil.str_cookies_to_list("foo=bar=baz", "example.com")

        assert len(result) == 1
        assert result[0]["name"] == "foo"
        assert result[0]["value"] == "bar=baz"

    def test_str_cookies_to_list_with_custom_params(self):
        """Test with custom parameters"""
        result = CookieUtil.str_cookies_to_list(
            "foo=bar", "example.com", path="/test", expires=123456, http_only=True, secure=True, same_site="Strict"
        )

        assert len(result) == 1
        assert result[0]["path"] == "/test"
        assert result[0]["expires"] == 123456
        assert result[0]["httpOnly"] is True
        assert result[0]["secure"] is True
        assert result[0]["sameSite"] == "Strict"

    def test_str_cookies_to_list_ignores_invalid(self):
        """Test that invalid parts are ignored"""
        result = CookieUtil.str_cookies_to_list("foo=bar; invalid; baz=qux", "example.com")

        assert len(result) == 2
