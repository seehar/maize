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
        cached_cookies = [{"name": "session", "value": "abc123"}]
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

    def test_status_default(self, mock_request):
        """Default status is 200."""
        response = Response(
            url="https://example.com",
            headers={},
            request=mock_request,
        )
        assert response.status == 200

    def test_text_from_body_decode(self, mock_request):
        """text property decodes body when no cached text."""
        response = Response(
            url="https://example.com",
            headers={},
            request=mock_request,
            body=b"hello world",
            status=200,
        )
        assert response.text == "hello world"

    def test_body_caches_after_decode_from_text(self, mock_request):
        """body property caches result after first encode from text."""
        response = Response(
            url="https://example.com",
            headers={},
            request=mock_request,
            text="cached",
            status=200,
        )
        first = response.body
        assert first == b"cached"
        assert response._body_cache == b"cached"

    def test_text_caches_after_decode_from_body(self, mock_request):
        """text property caches result after first decode from body."""
        response = Response(
            url="https://example.com",
            headers={},
            request=mock_request,
            body=b"hello",
            status=200,
        )
        first = response.text
        assert first == "hello"
        assert response._text_cache == "hello"

    def test_cookie_list_empty_when_no_set_cookie(self, mock_request):
        """cookie_list is empty when no Set-Cookie header and no cache."""
        response = Response(
            url="https://example.com",
            headers={},
            request=mock_request,
            status=200,
        )
        assert response.cookie_list == []

    def test_cookies_cached_after_first_access(self, mock_request):
        """cookies property caches dict after first access."""
        cached_cookies = [{"name": "a", "value": "1"}]
        response = Response(
            url="https://example.com",
            headers={},
            request=mock_request,
            cookie_list=cached_cookies,
            status=200,
        )
        first = response.cookies
        assert first == {"a": "1"}
        assert response._cookies_cache == {"a": "1"}

    def test_json_array(self, mock_request):
        """json() handles JSON arrays."""
        response = Response(
            url="https://example.com",
            headers={},
            request=mock_request,
            text="[1, 2, 3]",
            status=200,
        )
        result = response.json()
        assert result == [1, 2, 3]

    def test_json_number(self, mock_request):
        """json() handles JSON numbers."""
        response = Response(
            url="https://example.com",
            headers={},
            request=mock_request,
            text="42",
            status=200,
        )
        assert response.json() == 42

    def test_urljoin_absolute(self, mock_request):
        """urljoin with absolute URL returns the absolute URL."""
        response = Response(
            url="https://example.com/page",
            headers={},
            request=mock_request,
            status=200,
        )
        assert response.urljoin("https://other.com/path") == "https://other.com/path"

    def test_xpath_multiple_results(self, mock_request):
        """xpath returns multiple matching nodes."""
        response = Response(
            url="https://example.com",
            headers={},
            request=mock_request,
            text="<html><body><ul><li>a</li><li>b</li><li>c</li></ul></body></html>",
            status=200,
        )
        result = response.xpath("//li/text()")
        assert len(result) == 3
        assert result.getall() == ["a", "b", "c"]

    def test_xpath_caches_selector(self, mock_request):
        """xpath caches the Selector after first call."""
        response = Response(
            url="https://example.com",
            headers={},
            request=mock_request,
            text="<html></html>",
            status=200,
        )
        response.xpath("//html")
        assert response._selector is not None
        first_selector = response._selector
        response.xpath("//html")
        assert response._selector is first_selector

    def test_meta_reflects_request_meta(self, mock_request):
        """meta property returns request.meta."""
        mock_request.meta = {"depth": 3, "dont_filter": True}
        response = Response(
            url="https://example.com",
            headers={},
            request=mock_request,
            status=200,
        )
        assert response.meta == {"depth": 3, "dont_filter": True}

    def test_get_encoding_lowercase_content_type(self, mock_request):
        """_get_encoding handles lowercase content-type header."""
        response = Response(
            url="https://example.com",
            headers={"content-type": "text/html; charset=gbk"},
            request=mock_request,
            body=b"<html></html>",
            status=200,
        )
        assert response._get_encoding() == "gbk"

    def test_body_fallback_to_header_encoding_on_encode_error(self, mock_request):
        """body uses header charset when request.encoding fails."""
        mock_request.encoding = "ascii"
        response = Response(
            url="https://example.com",
            headers={"Content-Type": "text/html; charset=utf-8"},
            request=mock_request,
            text="héllo",
            status=200,
        )
        assert response.body == "héllo".encode()

    def test_text_fallback_to_header_encoding_on_decode_error(self, mock_request):
        """text uses header charset when request.encoding fails to decode."""
        mock_request.encoding = "ascii"
        response = Response(
            url="https://example.com",
            headers={"Content-Type": "text/html; charset=utf-8"},
            request=mock_request,
            body="héllo".encode(),
            status=200,
        )
        assert response.text == "héllo"
