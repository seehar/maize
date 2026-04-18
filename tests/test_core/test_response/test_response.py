"""
Tests for Response
"""

from unittest.mock import MagicMock

import pytest

from maize import Response
from maize.common.http.request import Request
from maize.exceptions.spider_exception import DecodeException, EncodeException


class TestResponse:
    """Test Response"""

    @pytest.fixture
    def mock_request(self):
        request = MagicMock(spec=Request)
        request.url = "https://example.com"
        request.encoding = "utf-8"
        request.meta = {"key": "value"}
        return request

    def test_str_representation(self, mock_request):
        """Test __str__ method"""
        response = Response(
            url="https://example.com",
            headers={},
            request=mock_request,
            status=200,
        )

        assert str(response) == "<200> https://example.com"

    def test_body_with_cached_body(self, mock_request):
        """Test body property with cached body"""
        response = Response(
            url="https://example.com",
            headers={},
            request=mock_request,
            body=b"cached body",
            status=200,
        )

        assert response.body == b"cached body"

    def test_body_from_text_cache(self, mock_request):
        """Test body property from text cache"""
        response = Response(
            url="https://example.com",
            headers={},
            request=mock_request,
            text="text content",
            status=200,
        )

        assert response.body == b"text content"

    def test_body_encode_error_fallback(self, mock_request):
        """Test body property handles encode error with fallback"""
        mock_request.encoding = "ascii"

        response = Response(
            url="https://example.com",
            headers={},
            request=mock_request,
            text="\xff\xfe",  # Invalid ascii
            status=200,
        )

        # Should raise EncodeException when encoding cannot be determined
        with pytest.raises(EncodeException):
            _ = response.body

    def test_text_with_cached_text(self, mock_request):
        """Test text property with cached text"""
        response = Response(
            url="https://example.com",
            headers={},
            request=mock_request,
            text="cached text",
            status=200,
        )

        assert response.text == "cached text"

    def test_text_decode_error_reraises(self, mock_request):
        """Test text property raises DecodeException when encoding cannot be determined"""
        mock_request.encoding = "ascii"

        response = Response(
            url="https://example.com",
            headers={},
            request=mock_request,
            body=b"\xff\xfe",  # Invalid ascii
            status=200,
        )

        # Should raise DecodeException when encoding cannot be determined
        with pytest.raises(DecodeException):
            _ = response.text

    def test_get_encoding_from_content_type_header(self, mock_request):
        """Test _get_encoding from Content-Type header"""
        response = Response(
            url="https://example.com",
            headers={"Content-Type": "text/html; charset=utf-8"},
            request=mock_request,
            body=b"<html></html>",
            status=200,
        )

        encoding = response._get_encoding()
        assert encoding == "utf-8"

    def test_get_encoding_from_content_type_header_gzip(self, mock_request):
        """Test _get_encoding ignores gzip content type"""
        response = Response(
            url="https://example.com",
            headers={"Content-Type": "application/gzip"},
            request=mock_request,
            body=b"<html></html>",
            status=200,
        )

        encoding = response._get_encoding()
        assert encoding is None

    def test_get_encoding_from_content_type_header_text(self, mock_request):
        """Test _get_encoding ignores text content type"""
        response = Response(
            url="https://example.com",
            headers={"Content-Type": "text/plain"},
            request=mock_request,
            body=b"<html></html>",
            status=200,
        )

        encoding = response._get_encoding()
        assert encoding is None

    def test_get_encoding_from_content_type_header_slash(self, mock_request):
        """Test _get_encoding ignores content type with slash"""
        response = Response(
            url="https://example.com",
            headers={"Content-Type": "text/"},
            request=mock_request,
            body=b"<html></html>",
            status=200,
        )

        encoding = response._get_encoding()
        assert encoding is None

    def test_get_encoding_from_body_charset(self, mock_request):
        """Test _get_encoding from body charset"""
        mock_request.encoding = "utf-8"
        response = Response(
            url="https://example.com",
            headers={},
            request=mock_request,
            body=b'<html><meta charset="gbk"></html>',
            status=200,
        )

        encoding = response._get_encoding()
        assert encoding == "gbk"

    def test_get_encoding_from_body_charset_quoted(self, mock_request):
        """Test _get_encoding from body charset in quotes"""
        mock_request.encoding = "utf-8"
        response = Response(
            url="https://example.com",
            headers={},
            request=mock_request,
            body=b'<html><meta charset="iso-8859-1"></html>',
            status=200,
        )

        encoding = response._get_encoding()
        assert encoding == "iso-8859-1"

    def test_get_encoding_not_found(self, mock_request):
        """Test _get_encoding returns None when not found"""
        response = Response(
            url="https://example.com",
            headers={},
            request=mock_request,
            body=b"<html></html>",
            status=200,
        )

        encoding = response._get_encoding()
        assert encoding is None

    def test_cookie_list_from_cache(self, mock_request):
        """Test cookie_list from cache"""
        cached_cookies = [{"name": "test", "value": "value"}]
        response = Response(
            url="https://example.com",
            headers={},
            request=mock_request,
            cookie_list=cached_cookies,
            status=200,
        )

        assert response.cookie_list == cached_cookies

    def test_cookie_list_from_set_cookie_header(self, mock_request):
        """Test cookie_list from Set-Cookie header"""
        response = Response(
            url="https://example.com",
            headers={"Set-Cookie": "session=abc123; path=/; HttpOnly"},
            request=mock_request,
            status=200,
        )

        cookies = response.cookie_list
        assert len(cookies) == 1
        assert cookies[0]["name"] == "session"
        assert cookies[0]["value"] == "abc123"

    def test_cookies_property(self, mock_request):
        """Test cookies property"""
        cached_cookies = [{"key": "session", "value": "abc123"}]
        response = Response(
            url="https://example.com",
            headers={},
            request=mock_request,
            cookie_list=cached_cookies,
            status=200,
        )

        cookies = response.cookies
        assert cookies == {"session": "abc123"}

    def test_json(self, mock_request):
        """Test json method"""
        response = Response(
            url="https://example.com",
            headers={},
            request=mock_request,
            text='{"key": "value"}',
            status=200,
        )

        result = response.json()
        assert result == {"key": "value"}

    def test_urljoin(self, mock_request):
        """Test urljoin method"""
        response = Response(
            url="https://example.com/page",
            headers={},
            request=mock_request,
            status=200,
        )

        result = response.urljoin("/relative")
        assert result == "https://example.com/relative"

    def test_xpath(self, mock_request):
        """Test xpath method"""
        response = Response(
            url="https://example.com",
            headers={},
            request=mock_request,
            text="<html><body><div>test</div></body></html>",
            status=200,
        )

        result = response.xpath("//div/text()")
        assert len(result) == 1

    def test_meta_property(self, mock_request):
        """Test meta property"""
        response = Response(
            url="https://example.com",
            headers={},
            request=mock_request,
            status=200,
        )

        assert response.meta == {"key": "value"}
