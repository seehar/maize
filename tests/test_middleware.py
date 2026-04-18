"""
Tests for the middleware system
"""

from unittest.mock import MagicMock

import pytest

from maize import SpiderSettings
from maize.common.constant import LogLevelEnum
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
    PipelineMiddlewareManager,
    SpiderMiddlewareManager,
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

    @pytest.mark.asyncio
    async def test_downloader_middleware_default_open_close(self):
        """Test DownloaderMiddleware open/close do nothing"""
        middleware = DownloaderMiddleware()
        # Should not raise
        await middleware.open()
        await middleware.close()

    @pytest.mark.asyncio
    async def test_downloader_middleware_default_process_request(self):
        """Test DownloaderMiddleware process_request returns request unchanged"""
        middleware = DownloaderMiddleware()
        request = Request(url="https://example.com")
        spider = MagicMock()

        result = await middleware.process_request(request, spider)

        assert result is request

    @pytest.mark.asyncio
    async def test_downloader_middleware_default_process_response(self):
        """Test DownloaderMiddleware process_response returns response unchanged"""
        middleware = DownloaderMiddleware()
        request = Request(url="https://example.com")
        response = MagicMock()
        response.__class__.__name__ = "Response"
        spider = MagicMock()

        result = await middleware.process_response(request, response, spider)

        assert result is response

    @pytest.mark.asyncio
    async def test_downloader_middleware_default_process_exception(self):
        """Test DownloaderMiddleware process_exception returns None"""
        middleware = DownloaderMiddleware()
        request = Request(url="https://example.com")
        exception = Exception("test")
        spider = MagicMock()

        result = await middleware.process_exception(request, exception, spider)

        assert result is None

    @pytest.mark.asyncio
    async def test_spider_middleware_default_open_close(self):
        """Test SpiderMiddleware open/close do nothing"""
        middleware = SpiderMiddleware()
        # Should not raise
        await middleware.open()
        await middleware.close()

    @pytest.mark.asyncio
    async def test_spider_middleware_default_process_spider_input(self):
        """Test SpiderMiddleware process_spider_input does nothing"""
        middleware = SpiderMiddleware()
        response = MagicMock()
        spider = MagicMock()

        result = await middleware.process_spider_input(response, spider)

        assert result is None

    @pytest.mark.asyncio
    async def test_spider_middleware_default_process_spider_output(self):
        """Test SpiderMiddleware process_spider_output yields items"""
        middleware = SpiderMiddleware()
        response = MagicMock()

        async def result_gen():
            yield "item1"
            yield "item2"

        result = middleware.process_spider_output(response, result_gen(), MagicMock())

        items = [item async for item in result]
        assert items == ["item1", "item2"]

    @pytest.mark.asyncio
    async def test_spider_middleware_default_process_spider_exception(self):
        """Test SpiderMiddleware process_spider_exception returns None"""
        middleware = SpiderMiddleware()
        response = MagicMock()
        exception = Exception("test")
        spider = MagicMock()

        result = await middleware.process_spider_exception(response, exception, spider)

        assert result is None

    @pytest.mark.asyncio
    async def test_spider_middleware_default_process_start_requests(self):
        """Test SpiderMiddleware process_start_requests yields requests"""
        middleware = SpiderMiddleware()

        async def requests_gen():
            yield Request(url="https://example.com/1")
            yield Request(url="https://example.com/2")

        result = middleware.process_start_requests(requests_gen(), MagicMock())

        items = [item async for item in result]
        assert len(items) == 2

    @pytest.mark.asyncio
    async def test_pipeline_middleware_default_open_close(self):
        """Test PipelineMiddleware open/close do nothing"""
        middleware = PipelineMiddleware()
        # Should not raise
        await middleware.open()
        await middleware.close()

    @pytest.mark.asyncio
    async def test_pipeline_middleware_default_process_item_before(self):
        """Test PipelineMiddleware process_item_before returns item unchanged"""
        middleware = PipelineMiddleware()
        item = ValidItem()
        item.title = "Test"
        spider = MagicMock()

        result = await middleware.process_item_before(item, spider)

        assert result is item

    @pytest.mark.asyncio
    async def test_pipeline_middleware_default_process_item_after(self):
        """Test PipelineMiddleware process_item_after returns item unchanged"""
        middleware = PipelineMiddleware()
        item = ValidItem()
        item.title = "Test"
        spider = MagicMock()

        result = await middleware.process_item_after(item, spider)

        assert result is item


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

    @pytest.mark.asyncio
    async def test_open_close_do_nothing(self):
        """Test that open and close do nothing"""
        middleware = DefaultHeadersMiddleware()
        # Should not raise
        await middleware.open()
        await middleware.close()

    def test_from_crawler(self):
        """Test from_crawler classmethod"""
        crawler = MagicMock()
        crawler.settings = MagicMock()
        crawler.settings.default_headers = {"X-Custom": "value"}

        middleware = DefaultHeadersMiddleware.from_crawler(crawler)

        assert middleware.default_headers.get("X-Custom") == "value"

    def test_custom_default_headers(self):
        """Test custom default headers"""
        custom_headers = {"X-Custom": "value", "Accept": "application/json"}
        middleware = DefaultHeadersMiddleware(default_headers=custom_headers)

        assert middleware.default_headers["X-Custom"] == "value"
        assert middleware.default_headers["Accept"] == "application/json"

    @pytest.mark.asyncio
    async def test_process_request_with_none_headers(self):
        """Test process_request handles None headers"""
        middleware = DefaultHeadersMiddleware()
        request = Request(url="https://example.com")
        request.headers = None
        spider = MagicMock()

        result = await middleware.process_request(request, spider)

        assert result.headers is not None
        assert "Accept" in result.headers


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

    @pytest.mark.asyncio
    async def test_does_not_retry_success_status(self):
        """Test that middleware does not retry success status codes"""
        middleware = RetryMiddleware(max_retry_count=3)
        request = Request(url="https://example.com")
        response = MagicMock()
        response.status = 200
        spider = MagicMock()

        result = await middleware.process_response(request, response, spider)

        # Should return response unchanged
        assert result is response
        assert request.meta.get("retry_count") is None

    @pytest.mark.asyncio
    async def test_retry_exception_matching_type(self):
        """Test that middleware retries on matching exception types"""
        middleware = RetryMiddleware(max_retry_count=3, retry_exceptions=[ConnectionError])
        request = Request(url="https://example.com")
        exception = ConnectionError("Connection failed")
        spider = MagicMock()

        result = await middleware.process_exception(request, exception, spider)

        assert result is request
        assert request.meta["retry_count"] == 1

    @pytest.mark.asyncio
    async def test_does_not_retry_non_matching_exception(self):
        """Test that middleware does not retry non-matching exceptions"""
        middleware = RetryMiddleware(max_retry_count=3, retry_exceptions=[ConnectionError])
        request = Request(url="https://example.com")
        exception = ValueError("Invalid value")
        spider = MagicMock()

        result = await middleware.process_exception(request, exception, spider)

        assert result is None

    def test_from_crawler(self):
        """Test from_crawler classmethod"""
        crawler = MagicMock()
        crawler.settings = MagicMock()
        crawler.settings.request = MagicMock()
        crawler.settings.request.max_retry_count = 5
        crawler.settings.retry_http_codes = [500, 502]
        crawler.settings.retry_exceptions = [Exception]
        crawler.settings.retry_delay = 1
        crawler.settings.exponential_backoff = True

        middleware = RetryMiddleware.from_crawler(crawler)

        assert middleware.max_retry_count == 5
        assert middleware.retry_http_codes == [500, 502]
        assert middleware.retry_exceptions == [Exception]
        assert middleware.retry_delay == 1
        assert middleware.exponential_backoff is True

    def test_get_retry_count_no_meta(self):
        """Test _get_retry_count when meta is None"""
        middleware = RetryMiddleware()

        request = MagicMock()
        request.meta = None

        count = middleware._get_retry_count(request)

        assert count == 0

    def test_get_retry_count_no_retry_in_meta(self):
        """Test _get_retry_count when meta has no retry_count"""
        middleware = RetryMiddleware()

        request = MagicMock()
        request.meta = {}

        count = middleware._get_retry_count(request)

        assert count == 0

    def test_get_retry_count_with_value(self):
        """Test _get_retry_count when meta has retry_count"""
        middleware = RetryMiddleware()

        request = MagicMock()
        request.meta = {"retry_count": 3}

        count = middleware._get_retry_count(request)

        assert count == 3

    def test_set_retry_count_creates_meta(self):
        """Test _set_retry_count creates meta if not exists"""
        middleware = RetryMiddleware()

        request = MagicMock()
        request.meta = None
        request._meta = None

        middleware._set_retry_count(request, 5)

        assert request._meta == {"retry_count": 5}

    @pytest.mark.asyncio
    async def test_calculate_delay_no_delay(self):
        """Test _calculate_delay returns 0 when retry_delay is 0"""
        middleware = RetryMiddleware(retry_delay=0)

        delay = await middleware._calculate_delay(3)

        assert delay == 0

    @pytest.mark.asyncio
    async def test_calculate_delay_linear(self):
        """Test _calculate_delay with linear backoff"""
        middleware = RetryMiddleware(retry_delay=1, exponential_backoff=False)

        delay = await middleware._calculate_delay(3)

        assert delay == 1

    @pytest.mark.asyncio
    async def test_calculate_delay_exponential(self):
        """Test _calculate_delay with exponential backoff"""
        middleware = RetryMiddleware(retry_delay=1, exponential_backoff=True)

        delay = await middleware._calculate_delay(3)

        assert delay == 8

    @pytest.mark.asyncio
    async def test_retry_request_gives_up_after_max(self):
        """Test _retry_request gives up after max retries"""
        middleware = RetryMiddleware(max_retry_count=2)
        middleware.logger = MagicMock()
        request = Request(url="https://example.com", meta={"retry_count": 2})

        result = await middleware._retry_request(request, "test", MagicMock())

        assert result is None
        middleware.logger.debug.assert_called()

    @pytest.mark.asyncio
    async def test_retry_request_updates_retry_count(self):
        """Test _retry_request updates retry count"""
        middleware = RetryMiddleware(max_retry_count=3)
        middleware.logger = MagicMock()
        request = Request(url="https://example.com")

        result = await middleware._retry_request(request, "test", MagicMock())

        assert result is request
        assert request.meta["retry_count"] == 1

    def test_default_retry_http_codes(self):
        """Test default retry HTTP codes"""
        middleware = RetryMiddleware()

        assert middleware.retry_http_codes == [500, 502, 503, 504, 408, 429]


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

    @pytest.mark.asyncio
    async def test_depth_priority_enabled(self):
        """Test that middleware adjusts priority when depth_priority_enabled"""
        middleware = DepthMiddleware(max_depth=5, depth_priority_enabled=True)
        middleware.logger = MagicMock()

        response = MagicMock()
        response.request = Request(url="https://example.com", meta={"depth": 0})
        spider = MagicMock()

        async def result_gen():
            req = Request(url="https://example.com/page1", priority=10)
            yield req

        result = middleware.process_spider_output(response, result_gen(), spider)

        items = [item async for item in result]
        assert len(items) == 1
        # Priority should be increased by depth (priority + new_depth = 10 + 1 = 11)
        assert items[0].priority == 11

    def test_from_crawler(self):
        """Test from_crawler classmethod"""
        crawler = MagicMock()
        crawler.settings = MagicMock()
        crawler.settings.max_depth = 10
        crawler.settings.depth_priority_enabled = True

        middleware = DepthMiddleware.from_crawler(crawler)

        assert middleware.max_depth == 10
        assert middleware.depth_priority_enabled is True

    def test_get_depth_no_meta(self):
        """Test _get_depth when request has no meta"""
        middleware = DepthMiddleware()

        request = MagicMock()
        request.meta = None

        depth = middleware._get_depth(request)

        assert depth == 0

    def test_get_depth_no_depth_in_meta(self):
        """Test _get_depth when meta has no depth key"""
        middleware = DepthMiddleware()

        request = MagicMock()
        request.meta = {}

        depth = middleware._get_depth(request)

        assert depth == 0

    def test_set_depth_creates_meta(self):
        """Test _set_depth creates meta if not exists"""
        middleware = DepthMiddleware()

        request = MagicMock()
        request.meta = None
        request._meta = None

        middleware._set_depth(request, 5)

        assert request._meta == {"depth": 5}

    @pytest.mark.asyncio
    async def test_process_start_requests_sets_depth_zero(self):
        """Test process_start_requests sets depth to 0"""
        middleware = DepthMiddleware()
        spider = MagicMock()

        async def requests_gen():
            yield Request(url="https://example.com")

        result = middleware.process_start_requests(requests_gen(), spider)

        items = [item async for item in result]
        assert len(items) == 1
        assert items[0].meta["depth"] == 0

    @pytest.mark.asyncio
    async def test_max_depth_zero_means_unlimited(self):
        """Test that max_depth=0 means unlimited depth"""
        middleware = DepthMiddleware(max_depth=0)

        response = MagicMock()
        response.request = Request(url="https://example.com", meta={"depth": 100})
        spider = MagicMock()

        async def result_gen():
            yield Request(url="https://example.com/page1")

        result = middleware.process_spider_output(response, result_gen(), spider)

        items = [item async for item in result]
        # Should allow even deep requests
        assert len(items) == 1


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

    @pytest.mark.asyncio
    async def test_allows_success_status(self):
        """Test that middleware allows success status codes"""
        middleware = HttpErrorMiddleware()
        response = MagicMock()
        response.status = 200
        response.url = "https://example.com"
        spider = MagicMock()

        result = await middleware.process_spider_input(response, spider)

        assert result is None

    @pytest.mark.asyncio
    async def test_denied_codes(self):
        """Test that middleware filters denied codes"""
        middleware = HttpErrorMiddleware(denied_codes=[200, 201])
        response = MagicMock()
        response.status = 200
        response.url = "https://example.com"
        spider = MagicMock()

        with pytest.raises(Exception, match="HTTP 200 error"):
            await middleware.process_spider_input(response, spider)

    @pytest.mark.asyncio
    async def test_custom_allowed_codes(self):
        """Test that middleware allows custom allowed codes"""
        middleware = HttpErrorMiddleware(allowed_codes=[200, 201, 202])
        response = MagicMock()
        response.status = 300
        response.url = "https://example.com"
        spider = MagicMock()

        with pytest.raises(Exception, match="HTTP 300 error"):
            await middleware.process_spider_input(response, spider)

    def test_from_crawler(self):
        """Test from_crawler classmethod"""
        crawler = MagicMock()
        crawler.settings = MagicMock()
        crawler.settings.http_error_allowed_codes = [200, 201]
        crawler.settings.http_error_denied_codes = [400, 404]
        crawler.settings.http_error_log_level = "info"

        middleware = HttpErrorMiddleware.from_crawler(crawler)

        assert middleware.allowed_codes == [200, 201]
        assert middleware.denied_codes == [400, 404]
        assert middleware.log_level == "info"

    @pytest.mark.asyncio
    async def test_close_with_stats(self):
        """Test close method with stats"""
        middleware = HttpErrorMiddleware()
        middleware.stats = {"http_error_404": 5, "http_error_500": 2}
        middleware.logger = MagicMock()

        await middleware.close()

        middleware.logger.info.assert_called()

    @pytest.mark.asyncio
    async def test_close_without_stats(self):
        """Test close method without stats"""
        middleware = HttpErrorMiddleware()
        middleware.stats = {}
        middleware.logger = MagicMock()

        await middleware.close()

        # Should not log if no stats
        middleware.logger.info.assert_not_called()

    @pytest.mark.asyncio
    async def test_should_filter_denied_codes(self):
        """Test _should_filter with denied codes"""
        middleware = HttpErrorMiddleware(denied_codes=[500])

        response = MagicMock()
        response.status = 500

        assert middleware._should_filter(response) is True

    @pytest.mark.asyncio
    async def test_should_filter_status_not_in_allowed(self):
        """Test _should_filter when status not in allowed codes"""
        middleware = HttpErrorMiddleware(allowed_codes=[200, 201])

        response = MagicMock()
        response.status = 300

        assert middleware._should_filter(response) is True

    @pytest.mark.asyncio
    async def test_should_filter_status_in_allowed(self):
        """Test _should_filter when status is in allowed codes"""
        middleware = HttpErrorMiddleware(allowed_codes=[200, 201])

        response = MagicMock()
        response.status = 200

        assert middleware._should_filter(response) is False

    @pytest.mark.asyncio
    async def test_log_error_debug(self):
        """Test _log_error with debug level"""
        middleware = HttpErrorMiddleware(log_level=LogLevelEnum.DEBUG.value)
        middleware.logger = MagicMock()
        middleware.stats = {}

        response = MagicMock()
        response.status = 404
        response.url = "https://example.com"

        middleware._log_error(response)

        middleware.logger.debug.assert_called()
        assert middleware.stats["http_error_404"] == 1

    @pytest.mark.asyncio
    async def test_log_error_info(self):
        """Test _log_error with info level"""
        middleware = HttpErrorMiddleware(log_level=LogLevelEnum.INFO.value)
        middleware.logger = MagicMock()
        middleware.stats = {}

        response = MagicMock()
        response.status = 500
        response.url = "https://example.com"

        middleware._log_error(response)

        middleware.logger.info.assert_called()
        assert middleware.stats["http_error_500"] == 1

    @pytest.mark.asyncio
    async def test_log_error_error(self):
        """Test _log_error with error level"""
        middleware = HttpErrorMiddleware(log_level=LogLevelEnum.ERROR.value)
        middleware.logger = MagicMock()
        middleware.stats = {}

        response = MagicMock()
        response.status = 502
        response.url = "https://example.com"

        middleware._log_error(response)

        middleware.logger.error.assert_called()


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

    @pytest.mark.asyncio
    async def test_validates_empty_required_field(self):
        """Test that middleware detects empty required fields"""
        middleware = ItemValidationMiddleware(required_fields=["title"])

        item = ValidItem()
        item.title = ""  # Empty string
        spider = MagicMock()

        result = await middleware.process_item_before(item, spider)
        assert result is None  # Should drop invalid item

    @pytest.mark.asyncio
    async def test_does_not_drop_invalid_when_configured(self):
        """Test that middleware doesn't drop invalid items when configured"""
        middleware = ItemValidationMiddleware(required_fields=["title"], drop_invalid_items=False)
        middleware.logger = MagicMock()

        item = ValidItem()
        item.title = "Test"
        # Missing 'url' which is required but we configured to not drop
        spider = MagicMock()

        result = await middleware.process_item_before(item, spider)
        assert result is item  # Returns item even though invalid

    def test_from_crawler(self):
        """Test from_crawler classmethod"""
        crawler = MagicMock()
        crawler.settings = MagicMock()
        crawler.settings.required_fields = ["title", "url"]
        crawler.settings.drop_invalid_items = False
        crawler.settings.validation_log_level = "info"

        middleware = ItemValidationMiddleware.from_crawler(crawler)

        assert middleware.required_fields == ["title", "url"]
        assert middleware.drop_invalid_items is False
        assert middleware.log_level == "info"

    def test_validate_item_missing_field(self):
        """Test _validate_item detects missing field"""
        middleware = ItemValidationMiddleware(required_fields=["title", "url"])

        item = ValidItem()
        item.title = "Test"
        # url is missing

        is_valid, errors = middleware._validate_item(item)

        assert is_valid is False
        assert any("url" in e for e in errors)

    def test_validate_item_empty_field(self):
        """Test _validate_item detects empty field"""
        middleware = ItemValidationMiddleware(required_fields=["title"])

        item = ValidItem()
        item.title = ""

        is_valid, errors = middleware._validate_item(item)

        assert is_valid is False
        assert any("empty" in e.lower() for e in errors)

    def test_validate_item_valid(self):
        """Test _validate_item passes valid item"""
        middleware = ItemValidationMiddleware(required_fields=["title", "url"])

        item = ValidItem()
        item.title = "Test"
        item.url = "https://example.com"

        is_valid, errors = middleware._validate_item(item)

        assert is_valid is True
        assert len(errors) == 0

    def test_log_validation_error_debug(self):
        """Test _log_validation_error with debug level"""
        middleware = ItemValidationMiddleware(log_level="debug")
        middleware.logger = MagicMock()

        middleware._log_validation_error(ValidItem(), ["error1", "error2"])

        middleware.logger.debug.assert_called()

    def test_log_validation_error_info(self):
        """Test _log_validation_error with info level"""
        middleware = ItemValidationMiddleware(log_level="info")
        middleware.logger = MagicMock()

        middleware._log_validation_error(ValidItem(), ["error1"])

        middleware.logger.info.assert_called()

    def test_log_validation_error_warning(self):
        """Test _log_validation_error with warning level"""
        middleware = ItemValidationMiddleware(log_level="warning")
        middleware.logger = MagicMock()

        middleware._log_validation_error(ValidItem(), ["error1"])

        middleware.logger.warning.assert_called()

    def test_log_validation_error_error(self):
        """Test _log_validation_error with error level"""
        middleware = ItemValidationMiddleware(log_level="error")
        middleware.logger = MagicMock()

        middleware._log_validation_error(ValidItem(), ["error1"])

        middleware.logger.error.assert_called()

    @pytest.mark.asyncio
    async def test_close_logs_stats(self):
        """Test close logs statistics"""
        middleware = ItemValidationMiddleware()
        middleware.logger = MagicMock()
        middleware.stats["items_validated"] = 10
        middleware.stats["items_invalid"] = 2
        middleware.stats["items_dropped"] = 1

        await middleware.close()

        middleware.logger.info.assert_called()

    @pytest.mark.asyncio
    async def test_stats_updated_on_validation(self):
        """Test that stats are updated during validation"""
        middleware = ItemValidationMiddleware(required_fields=["title"])

        item = ValidItem()
        item.title = "Test"
        spider = MagicMock()

        await middleware.process_item_before(item, spider)

        assert middleware.stats["items_validated"] == 1
        assert middleware.stats["items_invalid"] == 0
        assert middleware.stats["items_dropped"] == 0

    @pytest.mark.asyncio
    async def test_stats_updated_on_invalid_item(self):
        """Test that stats are updated when item is invalid"""
        middleware = ItemValidationMiddleware(required_fields=["title", "url"])

        item = ValidItem()
        item.title = "Test"
        # url missing
        spider = MagicMock()

        await middleware.process_item_before(item, spider)

        assert middleware.stats["items_validated"] == 1
        assert middleware.stats["items_invalid"] == 1
        assert middleware.stats["items_dropped"] == 1


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

    @pytest.mark.asyncio
    async def test_remove_html(self):
        """Test that middleware removes HTML tags"""
        middleware = ItemCleanerMiddleware(remove_html=True)

        item = ValidItem()
        item.title = "<b>Test</b> Title"
        spider = MagicMock()

        result = await middleware.process_item_before(item, spider)

        assert result.title == "Test Title"

    @pytest.mark.asyncio
    async def test_empty_to_none(self):
        """Test that middleware converts empty string to None"""
        middleware = ItemCleanerMiddleware(empty_to_none=True)

        item = ValidItem()
        item.title = ""
        spider = MagicMock()

        result = await middleware.process_item_before(item, spider)

        assert result.title is None

    @pytest.mark.asyncio
    async def test_excluded_fields(self):
        """Test that middleware excludes specified fields"""
        middleware = ItemCleanerMiddleware(strip_whitespace=True, excluded_fields=["title"])

        item = ValidItem()
        item.title = "  Test Title  "
        item.url = "  https://example.com  "
        spider = MagicMock()

        result = await middleware.process_item_before(item, spider)

        # title should not be stripped (excluded)
        assert result.title == "  Test Title  "
        # url should be stripped
        assert result.url == "https://example.com"

    @pytest.mark.asyncio
    async def test_clean_value_non_string(self):
        """Test that middleware doesn't modify non-string values"""
        middleware = ItemCleanerMiddleware(strip_whitespace=True)

        item = ValidItem()
        item.title = 123  # Integer should not be modified
        spider = MagicMock()

        result = await middleware.process_item_before(item, spider)

        assert result.title == 123

    @pytest.mark.asyncio
    async def test_clean_value_list(self):
        """Test that middleware cleans list values"""
        middleware = ItemCleanerMiddleware(strip_whitespace=True)

        item = ValidItem()
        item.title = ["  item1  ", "  item2  "]
        spider = MagicMock()

        result = await middleware.process_item_before(item, spider)

        assert result.title == ["item1", "item2"]

    def test_from_crawler(self):
        """Test from_crawler classmethod"""
        crawler = MagicMock()
        crawler.settings = MagicMock()
        crawler.settings.strip_whitespace = True
        crawler.settings.remove_html = True
        crawler.settings.normalize_whitespace = False
        crawler.settings.empty_to_none = True
        crawler.settings.excluded_fields = ["title"]

        middleware = ItemCleanerMiddleware.from_crawler(crawler)

        assert middleware.strip_whitespace is True
        assert middleware.remove_html is True
        assert middleware.normalize_whitespace is False
        assert middleware.empty_to_none is True
        assert middleware.excluded_fields == ["title"]

    @pytest.mark.asyncio
    async def test_combined_cleaning(self):
        """Test middleware with multiple cleaning options"""
        middleware = ItemCleanerMiddleware(
            strip_whitespace=True,
            remove_html=True,
            normalize_whitespace=True,
            empty_to_none=True,
        )

        item = ValidItem()
        item.title = "  <b>Test</b>   Title  "
        item.url = ""
        spider = MagicMock()

        result = await middleware.process_item_before(item, spider)

        assert result.title == "Test Title"
        assert result.url is None


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
        """Test that manager loads middleware"""
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

    @pytest.mark.asyncio
    async def test_process_response_chain(self):
        """Test that manager processes responses through chain"""
        crawler = MagicMock()
        crawler.settings = MagicMock()

        middlewares = {}

        manager = DownloaderMiddlewareManager(crawler, middlewares)
        await manager.open()

        request = Request(url="https://example.com")
        response = MagicMock()
        response.__class__.__name__ = "Response"
        spider = MagicMock()

        result = await manager.process_response(request, response, spider)

        assert result == response

    @pytest.mark.asyncio
    async def test_process_exception_chain(self):
        """Test that manager processes exceptions through chain"""
        crawler = MagicMock()
        crawler.settings = MagicMock()

        middlewares = {}

        manager = DownloaderMiddlewareManager(crawler, middlewares)
        await manager.open()

        request = Request(url="https://example.com")
        exception = Exception("test error")
        spider = MagicMock()

        result = await manager.process_exception(request, exception, spider)

        assert result is None

    @pytest.mark.asyncio
    async def test_middleware_close(self):
        """Test that manager closes all middlewares"""
        crawler = MagicMock()
        crawler.settings = MagicMock()

        middlewares = {
            "maize.middlewares.downloader.UserAgentMiddleware": 100,
        }

        manager = DownloaderMiddlewareManager(crawler, middlewares)
        await manager.open()
        await manager.close()

        assert len(manager.middlewares) == 1


class CustomSpiderMiddleware(SpiderMiddleware):
    async def process_spider_input(self, response, spider):
        pass

    async def process_spider_output(self, response, result, spider):
        async for item in result:
            yield item


class TestSpiderMiddlewareManager:
    """Test SpiderMiddlewareManager"""

    @pytest.mark.asyncio
    async def test_loads_middlewares(self):
        """Test that manager loads spider middlewares"""
        crawler = MagicMock()
        crawler.settings = MagicMock()

        middlewares = {
            "tests.test_middleware.CustomSpiderMiddleware": 100,
        }

        manager = SpiderMiddlewareManager(crawler, middlewares)
        await manager.open()

        assert len(manager.middlewares) == 1

    @pytest.mark.asyncio
    async def test_process_spider_input(self):
        """Test that manager processes spider input"""
        crawler = MagicMock()
        crawler.settings = MagicMock()

        middlewares = {
            "tests.test_middleware.CustomSpiderMiddleware": 100,
        }

        manager = SpiderMiddlewareManager(crawler, middlewares)
        await manager.open()

        response = MagicMock()
        spider = MagicMock()

        result = await manager.process_spider_input(response, spider)

        assert result is True

    @pytest.mark.asyncio
    async def test_process_spider_output(self):
        """Test that manager processes spider output"""
        crawler = MagicMock()
        crawler.settings = MagicMock()

        middlewares = {
            "tests.test_middleware.CustomSpiderMiddleware": 100,
        }

        manager = SpiderMiddlewareManager(crawler, middlewares)
        await manager.open()

        response = MagicMock()
        spider = MagicMock()

        async def generate_results():
            yield Request("https://example.com")

        result_gen = manager.process_spider_output(response, generate_results(), spider)

        items = [item async for item in result_gen]
        assert len(items) == 1


class CustomPipelineMiddleware(PipelineMiddleware):
    async def process_item_before(self, item, spider):
        return item

    async def process_item_after(self, item, spider):
        return item


class Response:
    """Mock Response class for testing"""

    pass


class CustomPipelineMiddlewareDropsItem(PipelineMiddleware):
    """Middleware that drops items"""

    async def process_item_before(self, item, spider):
        return None

    async def process_item_after(self, item, spider):
        return None


class TestPipelineMiddlewareManager:
    """Test PipelineMiddlewareManager"""

    @pytest.mark.asyncio
    async def test_loads_middlewares(self):
        """Test that manager loads pipeline middlewares"""
        crawler = MagicMock()
        crawler.settings = MagicMock()

        middlewares = {
            "tests.test_middleware.CustomPipelineMiddleware": 100,
        }

        manager = PipelineMiddlewareManager(crawler, middlewares)
        await manager.open()

        assert len(manager.middlewares) == 1

    @pytest.mark.asyncio
    async def test_process_item_before(self):
        """Test that manager processes item before pipeline"""
        crawler = MagicMock()
        crawler.settings = MagicMock()

        middlewares = {
            "tests.test_middleware.CustomPipelineMiddleware": 100,
        }

        manager = PipelineMiddlewareManager(crawler, middlewares)
        await manager.open()

        item = Item()
        spider = MagicMock()

        result = await manager.process_item_before(item, spider)

        assert result == item

    @pytest.mark.asyncio
    async def test_process_item_after(self):
        """Test that manager processes item after pipeline"""
        crawler = MagicMock()
        crawler.settings = MagicMock()

        middlewares = {
            "tests.test_middleware.CustomPipelineMiddleware": 100,
        }

        manager = PipelineMiddlewareManager(crawler, middlewares)
        await manager.open()

        item = Item()
        spider = MagicMock()

        result = await manager.process_item_after(item, spider)

        assert result == item

    @pytest.mark.asyncio
    async def test_process_item_before_drops_item(self):
        """Test that manager handles dropped items in process_item_before"""
        crawler = MagicMock()
        crawler.settings = MagicMock()

        middlewares = {
            "tests.test_middleware.CustomPipelineMiddlewareDropsItem": 100,
        }

        manager = PipelineMiddlewareManager(crawler, middlewares)
        await manager.open()

        item = Item()
        spider = MagicMock()

        result = await manager.process_item_before(item, spider)

        assert result is None

    @pytest.mark.asyncio
    async def test_process_item_after_drops_item(self):
        """Test that manager handles dropped items in process_item_after"""
        crawler = MagicMock()
        crawler.settings = MagicMock()

        middlewares = {
            "tests.test_middleware.CustomPipelineMiddlewareDropsItem": 100,
        }

        manager = PipelineMiddlewareManager(crawler, middlewares)
        await manager.open()

        item = Item()
        spider = MagicMock()

        result = await manager.process_item_after(item, spider)

        assert result is None


# ============================================================================
# Test MiddlewareManager error handling and boundary cases
# ============================================================================


class FailingDownloaderMiddleware(DownloaderMiddleware):
    """Middleware that fails on open/close"""

    async def open(self):
        raise Exception("Open failed")

    async def close(self):
        raise Exception("Close failed")


class FailingSpiderMiddleware(SpiderMiddleware):
    """Middleware that fails on process_spider_input"""

    async def process_spider_input(self, response, spider):
        raise Exception("Input processing failed")


class CustomDownloaderMiddlewareReturnsResponse(DownloaderMiddleware):
    """Middleware that returns a Response to stop chain"""

    async def process_request(self, request, spider):
        response = MagicMock()
        response.__class__.__name__ = "Response"
        return response


class CustomDownloaderMiddlewareDropsRequest(DownloaderMiddleware):
    """Middleware that returns None to drop request"""

    async def process_request(self, request, spider):
        return None


class CustomDownloaderMiddlewareReturnsRequest(DownloaderMiddleware):
    """Middleware that returns a Request for retry"""

    async def process_response(self, request, response, spider):
        return request


class CustomDownloaderMiddlewareDropsResponse(DownloaderMiddleware):
    """Middleware that returns None to drop response"""

    async def process_response(self, request, response, spider):
        return None


class CustomDownloaderMiddlewareHandlesException(DownloaderMiddleware):
    """Middleware that handles exception and returns Response"""

    async def process_exception(self, request, exception, spider):
        response = MagicMock()
        response.__class__.__name__ = "Response"
        return response


class FailingDownloaderMiddlewareProcessRequest(DownloaderMiddleware):
    """Middleware that fails on process_request"""

    async def process_request(self, request, spider):
        raise Exception("Process request failed")


class FailingDownloaderMiddlewareProcessResponse(DownloaderMiddleware):
    """Middleware that fails on process_response"""

    async def process_response(self, request, response, spider):
        raise Exception("Process response failed")


class FailingSpiderMiddlewareProcessOutput(SpiderMiddleware):
    """Middleware that fails on process_spider_output"""

    async def process_spider_output(self, response, result, spider):
        # Yield first item then raise to test exception during iteration
        async for item in result:
            yield item
            raise Exception("Process output failed")  # Raise after first item


class CustomSpiderMiddlewareHandlesException(SpiderMiddleware):
    """Middleware that handles exception"""

    async def process_spider_exception(self, response, exception, spider):
        async def result_gen():
            yield "handled"

        return result_gen()


class CustomSpiderMiddlewareReturnsResult(SpiderMiddleware):
    """Middleware that returns result from process_spider_exception"""

    async def process_spider_exception(self, response, exception, spider):
        async def result_gen():
            yield "handled"

        return result_gen()


class FailingSpiderMiddlewareProcessStartRequests(SpiderMiddleware):
    """Middleware that fails on process_start_requests"""

    async def process_start_requests(self, start_requests, spider):
        # Yield first item then raise to test exception during iteration
        async for request in start_requests:
            yield request
            raise Exception("Process start requests failed")  # Raise after first item


# Helper to create proper mock settings for logger
def create_mock_settings():
    settings = MagicMock()
    settings.log_level = "INFO"
    settings.log_format = "%(message)s"
    settings.logger_handler = None
    return settings


# Helper to mock logger handlers
def mock_logger_handlers(logger):
    """Mock logger handlers to avoid TypeError in level comparison"""
    mock_handler = MagicMock()
    mock_handler.level = 0
    logger.handlers = [mock_handler]
    return logger


class TestMiddlewareManagerOpenClose:
    """Test MiddlewareManager open/close error handling"""

    @pytest.mark.asyncio
    async def test_open_handles_middleware_failure(self):
        """Test that open handles middleware open failure gracefully"""
        crawler = MagicMock()
        crawler.settings = create_mock_settings()

        middlewares = {
            "tests.test_middleware.FailingDownloaderMiddleware": 100,
        }

        manager = DownloaderMiddlewareManager(crawler, middlewares)
        mock_logger_handlers(manager.logger)

        # Should not raise, just log error
        await manager.open()

        assert len(manager.middlewares) == 1

    @pytest.mark.asyncio
    async def test_close_handles_middleware_failure(self):
        """Test that close handles middleware close failure gracefully"""
        crawler = MagicMock()
        crawler.settings = create_mock_settings()

        middlewares = {
            "tests.test_middleware.FailingDownloaderMiddleware": 100,
        }

        manager = DownloaderMiddlewareManager(crawler, middlewares)
        mock_logger_handlers(manager.logger)
        await manager.open()
        # Should not raise, just log error
        await manager.close()


class TestDownloaderMiddlewareManagerBoundaryCases:
    """Test DownloaderMiddlewareManager boundary cases"""

    @pytest.mark.asyncio
    async def test_process_request_returns_response_stops_chain(self):
        """Test that returning Response stops the middleware chain"""
        crawler = MagicMock()
        crawler.settings = create_mock_settings()

        middlewares = {
            "tests.test_middleware.CustomDownloaderMiddlewareReturnsResponse": 100,
        }

        manager = DownloaderMiddlewareManager(crawler, middlewares)
        await manager.open()

        request = Request(url="https://example.com")
        spider = MagicMock()

        result = await manager.process_request(request, spider)

        assert result.__class__.__name__ == "Response"

    @pytest.mark.asyncio
    async def test_process_request_returns_none_drops_request(self):
        """Test that returning None drops the request"""
        crawler = MagicMock()
        crawler.settings = create_mock_settings()

        middlewares = {
            "tests.test_middleware.CustomDownloaderMiddlewareDropsRequest": 100,
        }

        manager = DownloaderMiddlewareManager(crawler, middlewares)
        await manager.open()

        request = Request(url="https://example.com")
        spider = MagicMock()

        result = await manager.process_request(request, spider)

        assert result is None

    @pytest.mark.asyncio
    async def test_process_request_exception_continues(self):
        """Test that exception in process_request continues to next middleware"""
        crawler = MagicMock()
        crawler.settings = create_mock_settings()

        middlewares = {
            "tests.test_middleware.FailingDownloaderMiddlewareProcessRequest": 100,
            "tests.test_middleware.CustomTestMiddleware": 200,
        }

        manager = DownloaderMiddlewareManager(crawler, middlewares)
        await manager.open()

        request = Request(url="https://example.com")
        spider = MagicMock()

        result = await manager.process_request(request, spider)

        # Should continue to next middleware and process
        assert result.meta.get("processed") is True

    @pytest.mark.asyncio
    async def test_process_response_returns_request_for_retry(self):
        """Test that returning Request signals retry"""
        crawler = MagicMock()
        crawler.settings = create_mock_settings()

        middlewares = {
            "tests.test_middleware.CustomDownloaderMiddlewareReturnsRequest": 100,
        }

        manager = DownloaderMiddlewareManager(crawler, middlewares)
        await manager.open()

        request = Request(url="https://example.com")
        response = MagicMock()
        response.__class__.__name__ = "Response"
        spider = MagicMock()

        result = await manager.process_response(request, response, spider)

        assert result.__class__.__name__ == "Request"

    @pytest.mark.asyncio
    async def test_process_response_returns_none_drops(self):
        """Test that returning None drops the response"""
        crawler = MagicMock()
        crawler.settings = create_mock_settings()

        middlewares = {
            "tests.test_middleware.CustomDownloaderMiddlewareDropsResponse": 100,
        }

        manager = DownloaderMiddlewareManager(crawler, middlewares)
        await manager.open()

        request = Request(url="https://example.com")
        response = MagicMock()
        response.__class__.__name__ = "Response"
        spider = MagicMock()

        result = await manager.process_response(request, response, spider)

        assert result is None

    @pytest.mark.asyncio
    async def test_process_response_exception_continues(self):
        """Test that exception in process_response continues"""
        crawler = MagicMock()
        crawler.settings = create_mock_settings()

        middlewares = {
            "tests.test_middleware.FailingDownloaderMiddlewareProcessResponse": 100,
        }

        manager = DownloaderMiddlewareManager(crawler, middlewares)
        mock_logger_handlers(manager.logger)
        await manager.open()

        request = Request(url="https://example.com")
        response = MagicMock()
        response.__class__.__name__ = "Response"
        spider = MagicMock()

        result = await manager.process_response(request, response, spider)

        # Should return response since exception was caught
        assert result == response

    @pytest.mark.asyncio
    async def test_process_exception_handles_and_returns(self):
        """Test that process_exception returning non-None stops chain"""
        crawler = MagicMock()
        crawler.settings = create_mock_settings()

        middlewares = {
            "tests.test_middleware.CustomDownloaderMiddlewareHandlesException": 100,
        }

        manager = DownloaderMiddlewareManager(crawler, middlewares)
        mock_logger_handlers(manager.logger)
        await manager.open()

        request = Request(url="https://example.com")
        exception = Exception("test error")
        spider = MagicMock()

        result = await manager.process_exception(request, exception, spider)

        assert result is not None

    @pytest.mark.asyncio
    async def test_process_exception_continues_on_error(self):
        """Test that exception in process_exception continues"""
        crawler = MagicMock()
        crawler.settings = create_mock_settings()

        class FailingDownloaderMiddlewareProcessException(DownloaderMiddleware):
            async def process_exception(self, request, exception, spider):
                raise Exception("Process exception failed")

        middlewares = {
            "tests.test_middleware.FailingDownloaderMiddlewareProcessException": 100,
        }

        manager = DownloaderMiddlewareManager(crawler, middlewares)
        mock_logger_handlers(manager.logger)
        await manager.open()

        request = Request(url="https://example.com")
        exception = Exception("test error")
        spider = MagicMock()

        result = await manager.process_exception(request, exception, spider)

        assert result is None


class TestSpiderMiddlewareManagerBoundaryCases:
    """Test SpiderMiddlewareManager boundary cases"""

    @pytest.mark.asyncio
    async def test_process_spider_input_raises_and_handled(self):
        """Test that exception in process_spider_input is handled"""
        crawler = MagicMock()
        crawler.settings = create_mock_settings()

        middlewares = {
            "tests.test_middleware.FailingSpiderMiddleware": 100,
        }

        manager = SpiderMiddlewareManager(crawler, middlewares)
        mock_logger_handlers(manager.logger)
        await manager.open()

        response = MagicMock()
        spider = MagicMock()

        # This should raise because no middleware handles the exception
        with pytest.raises(Exception, match="Input processing failed"):
            await manager.process_spider_input(response, spider)

    @pytest.mark.asyncio
    async def test_process_spider_output_exception_continues(self):
        """Test that exception in process_spider_output is propagated"""
        crawler = MagicMock()
        crawler.settings = create_mock_settings()

        middlewares = {
            "tests.test_middleware.FailingSpiderMiddlewareProcessOutput": 100,
        }

        manager = SpiderMiddlewareManager(crawler, middlewares)
        mock_logger_handlers(manager.logger)
        await manager.open()

        response = MagicMock()
        spider = MagicMock()

        async def generate_results():
            yield Request("https://example.com")

        result_gen = manager.process_spider_output(response, generate_results(), spider)

        # Exception propagates up, not caught by manager
        with pytest.raises(Exception, match="Process output failed"):
            [item async for item in result_gen]

    @pytest.mark.asyncio
    async def test_process_spider_exception_handles_and_returns(self):
        """Test that process_spider_exception returning result stops chain"""
        crawler = MagicMock()
        crawler.settings = create_mock_settings()

        middlewares = {
            "tests.test_middleware.CustomSpiderMiddlewareReturnsResult": 100,
        }

        manager = SpiderMiddlewareManager(crawler, middlewares)
        mock_logger_handlers(manager.logger)
        await manager.open()

        response = MagicMock()
        exception = Exception("test error")
        spider = MagicMock()

        result = await manager.process_spider_exception(response, exception, spider)

        assert result is not None

    @pytest.mark.asyncio
    async def test_process_spider_exception_continues_on_error(self):
        """Test that exception in process_spider_exception continues"""
        crawler = MagicMock()
        crawler.settings = create_mock_settings()

        class FailingSpiderMiddlewareProcessException(SpiderMiddleware):
            async def process_spider_exception(self, response, exception, spider):
                raise Exception("Process exception failed")

        middlewares = {
            "tests.test_middleware.FailingSpiderMiddlewareProcessException": 100,
        }

        manager = SpiderMiddlewareManager(crawler, middlewares)
        mock_logger_handlers(manager.logger)
        await manager.open()

        response = MagicMock()
        exception = Exception("test error")
        spider = MagicMock()

        result = await manager.process_spider_exception(response, exception, spider)

        assert result is None

    @pytest.mark.asyncio
    async def test_process_start_requests_exception_continues(self):
        """Test that exception in process_start_requests is propagated"""
        crawler = MagicMock()
        crawler.settings = create_mock_settings()

        middlewares = {
            "tests.test_middleware.FailingSpiderMiddlewareProcessStartRequests": 100,
        }

        manager = SpiderMiddlewareManager(crawler, middlewares)
        mock_logger_handlers(manager.logger)
        await manager.open()

        spider = MagicMock()

        async def generate_requests():
            yield Request("https://example.com")

        result_gen = manager.process_start_requests(generate_requests(), spider)

        # Exception propagates up, not caught by manager
        with pytest.raises(Exception, match="Process start requests failed"):
            [item async for item in result_gen]


class TestMiddlewareManagerLoadFailure:
    """Test MiddlewareManager loading failures"""

    @pytest.mark.asyncio
    async def test_load_middleware_with_invalid_path(self):
        """Test that manager handles invalid middleware path gracefully"""
        crawler = MagicMock()
        crawler.settings = create_mock_settings()

        middlewares = {
            "nonexistent.middleware.Path": 100,
        }

        manager = DownloaderMiddlewareManager(crawler, middlewares)
        # Should not raise, just log error
        await manager.open()

        # Middleware should not be loaded
        assert len(manager.middlewares) == 0


class MiddlewareWithoutFromCrawler:
    """Middleware that does not define from_crawler classmethod and does not inherit from BaseMiddleware"""

    def __init__(self, settings):
        self.settings = settings

    async def process_request(self, request, spider):
        return request


class TestMiddlewareLoadWithoutFromCrawler:
    """Test loading middleware without from_crawler classmethod"""

    @pytest.mark.asyncio
    async def test_load_middleware_without_from_crawler(self):
        """Test that middleware without from_crawler is instantiated with settings"""
        crawler = MagicMock()
        crawler.settings = create_mock_settings()

        middlewares = {
            "tests.test_middleware.MiddlewareWithoutFromCrawler": 100,
        }

        manager = DownloaderMiddlewareManager(crawler, middlewares)
        await manager.open()

        # Middleware should be loaded
        assert len(manager.middlewares) == 1
        middleware_instance = manager.middlewares[0][0]
        assert isinstance(middleware_instance, MiddlewareWithoutFromCrawler)
        assert middleware_instance.settings is crawler.settings
