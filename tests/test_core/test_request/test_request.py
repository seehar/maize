"""
Tests for Request.
"""

import pytest

from maize.common.constant.request_constant import Method
from maize.common.http.request import Request


class TestRequestBasics:
    """Test Request initialization, __str__, __lt__, defaults."""

    def test_default_values(self):
        req = Request("https://example.com")
        assert req.url == "https://example.com"
        assert req.method == "GET"
        assert req.priority == 0
        assert req.headers is None
        assert req.params is None
        assert req.data is None
        assert req.json is None
        assert req.cookies is None
        assert req.proxy is None
        assert req.encoding == "utf-8"
        assert req.follow_redirects is True
        assert req.max_redirects == 20
        assert req.meta == {}
        assert req.current_retry_count == 0

    def test_custom_method(self):
        req = Request("https://example.com", method=Method.POST)
        assert req.method == "POST"

    def test_str_representation(self):
        req = Request("https://example.com", method=Method.GET)
        assert str(req) == "GET https://example.com"

    def test_str_representation_post(self):
        req = Request("https://example.com", method=Method.POST)
        assert str(req) == "POST https://example.com"

    def test_str_representation_delete(self):
        req = Request("https://example.com", method=Method.DELETE)
        assert str(req) == "DELETE https://example.com"

    def test_lt_compares_priority(self):
        """asyncio.PriorityQueue is a min-heap: smaller priority = higher precedence."""
        low = Request("https://a.com", priority=10)
        high = Request("https://b.com", priority=1)
        # high < low because high.priority (1) < low.priority (10)
        assert high < low
        assert not (low < high)

    def test_lt_equal_priority(self):
        a = Request("https://a.com", priority=5)
        b = Request("https://b.com", priority=5)
        assert not (a < b)
        assert not (b < a)

    def test_meta_defaults_to_empty_dict(self):
        req = Request("https://example.com")
        assert req.meta == {}

    def test_meta_custom_value(self):
        req = Request("https://example.com", meta={"key": "value"})
        assert req.meta == {"key": "value"}

    def test_meta_shared_reference_is_safe(self):
        """Each Request gets its own meta dict by default."""
        a = Request("https://a.com")
        b = Request("https://b.com")
        a.meta["x"] = 1
        assert "x" not in b.meta


class TestRequestRetry:
    """Test retry counting."""

    def test_initial_retry_count_is_zero(self):
        req = Request("https://example.com")
        assert req.current_retry_count == 0

    def test_retry_increments_count(self):
        req = Request("https://example.com")
        req.retry()
        assert req.current_retry_count == 1
        req.retry()
        assert req.current_retry_count == 2


class TestRequestHash:
    """Test Request.hash dedup property."""

    def test_same_url_method_produces_same_hash(self):
        a = Request("https://example.com")
        b = Request("https://example.com")
        assert a.hash == b.hash

    def test_different_url_produces_different_hash(self):
        a = Request("https://example.com/a")
        b = Request("https://example.com/b")
        assert a.hash != b.hash

    def test_different_method_produces_different_hash(self):
        a = Request("https://example.com", method=Method.GET)
        b = Request("https://example.com", method=Method.POST)
        assert a.hash != b.hash

    def test_different_params_produces_different_hash(self):
        a = Request("https://example.com", params={"page": 1})
        b = Request("https://example.com", params={"page": 2})
        assert a.hash != b.hash

    def test_different_data_produces_different_hash(self):
        a = Request("https://example.com", data={"q": "a"})
        b = Request("https://example.com", data={"q": "b"})
        assert a.hash != b.hash

    def test_different_json_produces_different_hash(self):
        """POST+JSON with different body must produce different hash (bug fix coverage)."""
        a = Request("https://example.com", json={"page": 1})
        b = Request("https://example.com", json={"page": 2})
        assert a.hash != b.hash

    def test_same_json_produces_same_hash(self):
        a = Request("https://example.com", json={"page": 1})
        b = Request("https://example.com", json={"page": 1})
        assert a.hash == b.hash

    def test_different_headers_produce_different_hash(self):
        """headers with different values produce different hash."""
        a = Request("https://example.com", headers={"X-Token": "a"})
        b = Request("https://example.com", headers={"X-Token": "b"})
        assert a.hash != b.hash

    def test_same_headers_produce_same_hash(self):
        a = Request("https://example.com", headers={"X-Token": "a"})
        b = Request("https://example.com", headers={"X-Token": "a"})
        assert a.hash == b.hash

    def test_none_headers_hash_consistent(self):
        """None headers and empty string headers should hash consistently."""
        a = Request("https://example.com")
        b = Request("https://example.com", headers=None)
        assert a.hash == b.hash

    def test_hash_is_hex_string(self):
        req = Request("https://example.com")
        h = req.hash
        assert isinstance(h, str)
        assert len(h) == 32  # md5 hex digest


class TestRequestModelDump:
    """Test Request.model_dump."""

    def test_model_dump_contains_expected_keys(self):
        req = Request(
            "https://example.com",
            method=Method.POST,
            priority=5,
            headers={"X-Test": "1"},
            params={"q": "test"},
            data={"body": "x"},
            cookies={"session": "abc"},
            proxy="http://proxy:8080",
        )
        dumped = req.model_dump
        assert dumped["url"] == "https://example.com"
        assert dumped["method"] == "POST"
        assert dumped["priority"] == 5
        assert dumped["headers"] == {"X-Test": "1"}
        assert dumped["params"] == {"q": "test"}
        assert dumped["data"] == {"body": "x"}
        assert dumped["cookies"] == {"session": "abc"}
        assert dumped["proxy"] == "http://proxy:8080"

    def test_model_dump_callback_name(self):
        def my_callback(response):
            pass

        req = Request("https://example.com", callback=my_callback)
        assert req.model_dump["callback"] == "my_callback"

    def test_model_dump_callback_none(self):
        req = Request("https://example.com")
        assert req.model_dump["callback"] is None


class TestRequestGetHeaders:
    """Test Request.get_headers."""

    @pytest.mark.asyncio
    async def test_get_headers_returns_static_headers(self):
        req = Request("https://example.com", headers={"X-Test": "1"})
        assert await req.get_headers() == {"X-Test": "1"}

    @pytest.mark.asyncio
    async def test_get_headers_returns_none_when_no_headers(self):
        req = Request("https://example.com")
        assert await req.get_headers() is None

    @pytest.mark.asyncio
    async def test_get_headers_uses_headers_func(self):
        async def custom_headers():
            return {"X-Dynamic": "yes"}

        req = Request("https://example.com", headers_func=custom_headers)
        assert await req.get_headers() == {"X-Dynamic": "yes"}

    @pytest.mark.asyncio
    async def test_get_headers_func_overrides_static(self):
        async def custom_headers():
            return {"X-Dynamic": "yes"}

        req = Request("https://example.com", headers={"X-Static": "1"}, headers_func=custom_headers)
        assert await req.get_headers() == {"X-Dynamic": "yes"}
