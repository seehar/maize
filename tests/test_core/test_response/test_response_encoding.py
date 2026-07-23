"""
Tests for Response encoding fallback paths.
"""

import pytest

from maize.common.constant.request_constant import Method
from maize.common.http.request import Request
from maize.common.http.response import Response
from maize.exceptions.spider_exception import DecodeException, EncodeException


def _make_request(encoding="utf-8"):
    return Request("https://example.com", method=Method.GET, encoding=encoding)


class TestResponseBodyEncodeFallback:
    """Test body property encode error fallback paths."""

    def test_body_encode_error_raises_when_no_encoding_found(self):
        """body with text that can't encode and no charset in headers/body -> EncodeException."""
        req = _make_request("ascii")
        # Text with non-ascii char, no charset in headers or body to fall back to
        resp = Response(
            url="https://example.com",
            headers={},
            request=req,
            text="héllo",
            status=200,
        )
        with pytest.raises(EncodeException):
            _ = resp.body

    def test_body_uses_header_charset_on_encode_error(self):
        """body falls back to charset from Content-Type header."""
        req = _make_request("ascii")
        resp = Response(
            url="https://example.com",
            headers={"Content-Type": "text/html; charset=utf-8"},
            request=req,
            text="héllo",
            status=200,
        )
        assert resp.body == "héllo".encode()


class TestResponseTextDecodeFallback:
    """Test text property decode error fallback paths."""

    def test_text_decode_error_raises_when_no_encoding_found(self):
        """text with body that can't decode and no charset -> DecodeException."""
        req = _make_request("ascii")
        resp = Response(
            url="https://example.com",
            headers={},
            request=req,
            body=b"\xff\xfe",
            status=200,
        )
        with pytest.raises(DecodeException):
            _ = resp.text

    def test_text_uses_header_charset_on_decode_error(self):
        """text falls back to charset from Content-Type header."""
        req = _make_request("ascii")
        resp = Response(
            url="https://example.com",
            headers={"Content-Type": "text/html; charset=utf-8"},
            request=req,
            body="héllo".encode(),
            status=200,
        )
        assert resp.text == "héllo"

    def test_text_uses_body_charset_on_decode_error(self):
        """text falls back to charset found in body content."""
        req = _make_request("ascii")
        resp = Response(
            url="https://example.com",
            headers={},
            request=req,
            body='<meta charset="utf-8">héllo'.encode(),
            status=200,
        )
        assert "héllo" in resp.text

    def test_text_uses_quoted_body_charset_on_decode_error(self):
        """text falls back to quoted charset in body."""
        req = _make_request("ascii")
        resp = Response(
            url="https://example.com",
            headers={},
            request=req,
            body='<meta charset="utf-8">héllo'.encode(),
            status=200,
        )
        assert "héllo" in resp.text
