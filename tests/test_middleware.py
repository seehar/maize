"""
Tests for the middleware system
"""

from unittest.mock import MagicMock

import pytest

from maize import SpiderSettings
from maize.common.http.request import Request
from maize.common.items import Item
from maize.middlewares.base_middleware import (
    DownloaderMiddleware,
    PipelineMiddleware,
    SpiderMiddleware,
)
from maize.middlewares.downloader import (
    DefaultHeadersMiddleware,
    RetryMiddleware,
    UserAgentMiddleware,
)
from maize.middlewares.middleware_manager import (
    DownloaderMiddlewareManager,
)
from maize.middlewares.pipeline import (
    ItemCleanerMiddleware,
    ItemValidationMiddleware,
)
from maize.middlewares.spider import (
    DepthMiddleware,
    HttpErrorMiddleware,
)
from maize.utils.log_util import set_spider_settings

# ============================================================================
# Test Base Middlewares
# ============================================================================


class TestBaseMiddleware:
    """Test base middleware classes"""

    @staticmethod
    def setup_method():
        settings = SpiderSettings()
        set_spider_settings(settings)

    def test_downloader_middleware_interface(self):
        """Test DownloaderMiddleware has correct methods"""
        middleware = DownloaderMiddleware()
        assert hasattr(middleware, "process_request")
        assert hasattr(middleware, "process_response")
        assert hasattr(middleware, "process_exception")
        assert hasattr(middleware, "open")
        assert hasattr(middleware, "close")

    def test_spider_middleware_interface(self):
        """Test SpiderMiddleware has correct methods"""
        middleware = SpiderMiddleware()
        assert hasattr(middleware, "process_spider_input")
        assert hasattr(middleware, "process_spider_output")
        assert hasattr(middleware, "process_spider_exception")
        assert hasattr(middleware, "process_start_requests")

    def test_pipeline_middleware_interface(self):
        """Test PipelineMiddleware has correct methods"""
        middleware = PipelineMiddleware()
        assert hasattr(middleware, "process_item_before")
        assert hasattr(middleware, "process_item_after")


# ============================================================================
# Test Downloader Middlewares
# ============================================================================


class TestUserAgentMiddleware:
    """Test UserAgentMiddleware"""

    @staticmethod
    def setup_method():
        settings = SpiderSettings()
        set_spider_settings(settings)

    @pytest.mark.asyncio
    async def test_adds_user_agent(self):
        """Test that middleware adds User-Agent header"""
        middleware = UserAgentMiddleware()
        request = Request(url="https://example.com")
        spider = MagicMock()

        result = await middleware.process_request(request, spider)

        assert result.headers is not None
        assert "User-Agent" in result.headers

    @pytest.mark.asyncio
    async def test_respects_existing_user_agent(self):
        """Test that middleware doesn't override existing User-Agent"""
        middleware = UserAgentMiddleware()
        custom_ua = "CustomBot/1.0"
        request = Request(url="https://example.com", headers={"User-Agent": custom_ua})
        spider = MagicMock()

        result = await middleware.process_request(request, spider)

        assert result.headers["User-Agent"] == custom_ua


class TestDefaultHeadersMiddleware:
    """Test DefaultHeadersMiddleware"""

    @staticmethod
    def setup_method():
        settings = SpiderSettings()
        set_spider_settings(settings)

    @pytest.mark.asyncio
    async def test_adds_default_headers(self):
        """Test that middleware adds default headers"""
        middleware = DefaultHeadersMiddleware()
        request = Request(url="https://example.com")
        spider = MagicMock()

        result = await middleware.process_request(request, spider)

        assert result.headers is not None
        assert "Accept" in result.headers

    @pytest.mark.asyncio
    async def test_respects_existing_headers(self):
        """Test that middleware doesn't override existing headers"""
        middleware = DefaultHeadersMiddleware()
        custom_accept = "application/json"
        request = Request(url="https://example.com", headers={"Accept": custom_accept})
        spider = MagicMock()

        result = await middleware.process_request(request, spider)

        assert result.headers["Accept"] == custom_accept


class TestRetryMiddleware:
    """Test RetryMiddleware"""

    @staticmethod
    def setup_method():
        settings = SpiderSettings()
        set_spider_settings(settings)

    @pytest.mark.asyncio
    async def test_retries_on_error_status(self):
        """Test that middleware retries on error status codes"""
        middleware = RetryMiddleware(max_retry_count=3)
        request = Request(url="https://example.com")
        response = MagicMock()
        response.status = 500
        spider = MagicMock()

        result = await middleware.process_response(request, response, spider)

        # Should return the same request for retry
        assert result is request
        assert request.meta["retry_count"] == 1

    @pytest.mark.asyncio
    async def test_gives_up_after_max_retries(self):
        """Test that middleware gives up after max retries"""
        middleware = RetryMiddleware(max_retry_count=2)
        request = Request(url="https://example.com", meta={"retry_count": 2})
        response = MagicMock()
        response.status = 500
        spider = MagicMock()

        result = await middleware.process_response(request, response, spider)

        # Should return None (give up)
        assert result is None


# ============================================================================
# Test Spider Middlewares
# ============================================================================


class TestDepthMiddleware:
    """Test DepthMiddleware"""

    @staticmethod
    def setup_method():
        settings = SpiderSettings()
        set_spider_settings(settings)

    @pytest.mark.asyncio
    async def test_filters_by_depth(self):
        """Test that middleware filters requests by depth"""
        middleware = DepthMiddleware(max_depth=2)

        # Create a response with depth 2 (at the limit)
        response = MagicMock()
        response.request = Request(url="https://example.com", meta={"depth": 2})
        spider = MagicMock()

        # Create a generator that yields requests
        # Since response.request has depth=2, the new request will have depth=3
        # which exceeds max_depth=2, so it should be filtered
        async def result_gen():
            req = Request(url="https://example.com/page1")
            yield req

        result = middleware.process_spider_output(response, result_gen(), spider)

        # Should filter out the request because depth 3 > max_depth 2
        items = [item async for item in result]
        assert len(items) == 0

    @pytest.mark.asyncio
    async def test_allows_within_depth(self):
        """Test that middleware allows requests within depth limit"""
        middleware = DepthMiddleware(max_depth=3)

        # Create a response with depth 1
        response = MagicMock()
        response.request = Request(url="https://example.com", meta={"depth": 1})
        spider = MagicMock()

        # Create a generator that yields requests
        # Since response.request has depth=1, the new request will have depth=2
        # which is within max_depth=3, so it should pass
        async def result_gen():
            req = Request(url="https://example.com/page1")
            yield req

        result = middleware.process_spider_output(response, result_gen(), spider)

        # Should allow the request because depth 2 <= max_depth 3
        items = [item async for item in result]
        assert len(items) == 1
        # Check that depth was set correctly
        assert items[0].meta["depth"] == 2


class TestHttpErrorMiddleware:
    """Test HttpErrorMiddleware"""

    @staticmethod
    def setup_method():
        settings = SpiderSettings()
        set_spider_settings(settings)

    @pytest.mark.asyncio
    async def test_filters_error_status(self):
        """Test that middleware filters error status codes"""
        middleware = HttpErrorMiddleware()
        response = MagicMock()
        response.status = 404
        response.url = "https://example.com"
        spider = MagicMock()

        with pytest.raises(Exception, match="HTTP 404 error"):
            await middleware.process_spider_input(response, spider)


# ============================================================================
# Test Pipeline Middlewares
# ============================================================================


class ValidItem(Item):
    title: str = ""
    url: str = ""


class TestItemValidationMiddleware:
    """Test ItemValidationMiddleware"""

    @staticmethod
    def setup_method():
        settings = SpiderSettings()
        set_spider_settings(settings)

    @pytest.mark.asyncio
    async def test_validates_required_fields(self):
        """Test that middleware validates required fields"""
        middleware = ItemValidationMiddleware(required_fields=["title", "url"])

        # Valid item
        valid_item = ValidItem()
        valid_item.title = "Test"
        valid_item.url = "https://example.com"
        spider = MagicMock()

        result = await middleware.process_item_before(valid_item, spider)
        assert result is valid_item

        # Invalid item (missing field)
        invalid_item = ValidItem()
        invalid_item.title = "Test"
        spider = MagicMock()

        result = await middleware.process_item_before(invalid_item, spider)
        assert result is None  # Should drop invalid item


class TestItemCleanerMiddleware:
    """Test ItemCleanerMiddleware"""

    @staticmethod
    def setup_method():
        settings = SpiderSettings()
        set_spider_settings(settings)

    @pytest.mark.asyncio
    async def test_strips_whitespace(self):
        """Test that middleware strips whitespace"""
        middleware = ItemCleanerMiddleware(strip_whitespace=True)

        item = ValidItem()
        item.title = "  Test Title  "
        spider = MagicMock()

        result = await middleware.process_item_before(item, spider)

        assert result.title == "Test Title"

    @pytest.mark.asyncio
    async def test_normalizes_whitespace(self):
        """Test that middleware normalizes whitespace"""
        middleware = ItemCleanerMiddleware(normalize_whitespace=True)

        item = ValidItem()
        item.title = "Test   Title"
        spider = MagicMock()

        result = await middleware.process_item_before(item, spider)

        assert result.title == "Test Title"


# ============================================================================
# Test Middleware Managers
# ============================================================================
class CustomTestMiddleware(DownloaderMiddleware):
    async def process_request(self, request, spider):
        request._meta = {"processed": True}
        return request


class TestDownloaderMiddlewareManager:
    """Test DownloaderMiddlewareManager"""

    @pytest.mark.asyncio
    async def test_loads_middlewares(self):
        """Test that manager loads middlewares"""
        crawler = MagicMock()
        crawler.settings = MagicMock()
        middlewares = {
            "maize.middlewares.downloader.UserAgentMiddleware": 100,
        }

        manager = DownloaderMiddlewareManager(crawler, middlewares)
        await manager.open()

        assert len(manager.middlewares) == 1

    @pytest.mark.asyncio
    async def test_process_request_chain(self):
        """Test that manager processes requests through chain"""
        crawler = MagicMock()
        crawler.settings = MagicMock()

        # Create custom middleware for testing

        middlewares = {
            "tests.test_middleware.CustomTestMiddleware": 100,
        }

        manager = DownloaderMiddlewareManager(crawler, middlewares)
        await manager.open()

        request = Request(url="https://example.com")
        spider = MagicMock()

        result = await manager.process_request(request, spider)

        assert result.meta["processed"] is True
