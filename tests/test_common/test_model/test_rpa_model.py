"""
Tests for rpa_model InterceptRequest and InterceptResponse.
"""

from maize.common.model.rpa_model import InterceptRequest, InterceptResponse


class TestInterceptRequest:
    """Test InterceptRequest."""

    def test_init_with_all_fields(self):
        req = InterceptRequest(
            url="https://example.com/api",
            data=b'{"key": "value"}',
            headers={"Content-Type": "application/json"},
        )
        assert req.url == "https://example.com/api"
        assert req.data == b'{"key": "value"}'
        assert req.headers == {"Content-Type": "application/json"}

    def test_init_with_none_data(self):
        req = InterceptRequest(url="https://example.com", data=None, headers={})
        assert req.url == "https://example.com"
        assert req.data is None
        assert req.headers == {}

    def test_fields_are_mutable(self):
        req = InterceptRequest(url="https://example.com", data=b"", headers={})
        req.url = "https://changed.com"
        req.data = b"new data"
        req.headers = {"X-Test": "1"}
        assert req.url == "https://changed.com"
        assert req.data == b"new data"
        assert req.headers == {"X-Test": "1"}


class TestInterceptResponse:
    """Test InterceptResponse."""

    def _make_request(self):
        return InterceptRequest(url="https://example.com", data=None, headers={})

    def test_init_with_all_fields(self):
        req = self._make_request()
        resp = InterceptResponse(
            request=req,
            url="https://example.com/response",
            headers={"Content-Type": "text/html"},
            content=b"<html>body</html>",
            status_code=200,
        )
        assert resp.request is req
        assert resp.url == "https://example.com/response"
        assert resp.headers == {"Content-Type": "text/html"}
        assert resp.content == b"<html>body</html>"
        assert resp.status_code == 200

    def test_init_with_none_content(self):
        req = self._make_request()
        resp = InterceptResponse(
            request=req,
            url="https://example.com",
            headers={},
            content=None,
            status_code=404,
        )
        assert resp.content is None
        assert resp.status_code == 404

    def test_fields_are_mutable(self):
        req = self._make_request()
        resp = InterceptResponse(
            request=req,
            url="https://example.com",
            headers={},
            content=b"",
            status_code=200,
        )
        resp.url = "https://changed.com"
        resp.status_code = 500
        resp.content = b"error"
        assert resp.url == "https://changed.com"
        assert resp.status_code == 500
        assert resp.content == b"error"

    def test_request_reference_preserved(self):
        """The request field holds a direct reference, not a copy."""
        req = InterceptRequest(url="https://example.com", data=b"data", headers={"H": "V"})
        resp = InterceptResponse(
            request=req,
            url="https://example.com",
            headers={},
            content=b"",
            status_code=200,
        )
        assert resp.request is req
        assert resp.request.url == "https://example.com"
        assert resp.request.data == b"data"
