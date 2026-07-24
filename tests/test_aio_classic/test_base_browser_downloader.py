"""BaseBrowserDownloader 覆盖率测试（mock 驱动，无需真实浏览器）。"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from maize import Request, SpiderSettings
from maize.aio.classic.downloader.base_browser_downloader import BaseBrowserDownloader
from maize.common.model.download_response_model import DownloadResponse
from maize.common.model.rpa_model import InterceptRequest, InterceptResponse
from maize.utils.log_util import set_spider_settings


class _FakeViewportSize:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height


class _ConcreteBrowserDownloader(BaseBrowserDownloader):
    """用于测试的具体子类。"""

    async def _get_playwright_instance(self):
        return self._fake_playwright_context

    def _get_viewport_size_class(self):
        return _FakeViewportSize


def _make_crawler(**rpa_overrides):
    """构造带 mock 的 Crawler 对象。"""
    settings = SpiderSettings()
    # 覆盖 RPA 配置
    rpa = settings.rpa
    for key, value in rpa_overrides.items():
        setattr(rpa, key, value)

    crawler = MagicMock()
    crawler.settings = settings
    crawler.spider = MagicMock()
    crawler.spider.__str__ = lambda _: "TestSpider"
    return crawler


@pytest.fixture(autouse=True)
def _setup():
    set_spider_settings(SpiderSettings())


# --- __init__ ---


class TestInit:
    def test_init_basic(self):
        crawler = _make_crawler()
        dl = _ConcreteBrowserDownloader(crawler)
        assert dl.playwright is None
        assert dl.browser is None
        assert dl.context is None
        assert dl.page_pool is None
        assert dl._cache_data == {}
        assert dl._context_route_initialized is False

    def test_init_url_regexes_save_all_warning(self):
        crawler = _make_crawler(url_regexes=["api/.*"], url_regexes_save_all=True)
        dl = _ConcreteBrowserDownloader(crawler)
        assert dl._cache_data == {}


# --- open ---


class TestOpen:
    @pytest.mark.asyncio
    async def test_open_no_session(self):
        crawler = _make_crawler()
        crawler.settings.request.use_session = False
        dl = _ConcreteBrowserDownloader(crawler)
        await dl.open()
        assert dl.page_pool is not None
        assert dl._use_session is False
        assert dl.browser is None

    @pytest.mark.asyncio
    async def test_open_with_session(self):
        crawler = _make_crawler()
        crawler.settings.request.use_session = True
        dl = _ConcreteBrowserDownloader(crawler)

        fake_pw = MagicMock()
        fake_pw.start = AsyncMock(return_value=MagicMock())
        dl._fake_playwright_context = fake_pw

        fake_context = MagicMock()
        fake_context.add_init_script = AsyncMock()
        fake_context.route = MagicMock(return_value=None)

        fake_browser = MagicMock()
        fake_browser.new_context = AsyncMock(return_value=fake_context)

        with patch.object(dl, "_get_browser", new_callable=AsyncMock, return_value=fake_browser):
            await dl.open()

        assert dl.playwright is not None
        assert dl.browser is fake_browser


# --- on_response ---


class TestOnResponse:
    @pytest.mark.asyncio
    async def test_on_response_matching(self):
        crawler = _make_crawler(url_regexes=["api/data"])
        dl = _ConcreteBrowserDownloader(crawler)

        response = MagicMock()
        response.request.url = "http://example.com/api/data?page=1"
        response.request.headers = {"Content-Type": "application/json"}
        response.request.post_data_buffer = None
        response.url = "http://example.com/api/data?page=1"
        response.headers = {"Content-Type": "application/json"}
        response.body = AsyncMock(return_value=b'{"key": "value"}')
        response.status = 200

        await dl.on_response(response)
        assert "api/data" in dl._cache_data
        assert len(dl._cache_data["api/data"]) == 1
        assert dl._cache_data["api/data"][0].content == b'{"key": "value"}'

    @pytest.mark.asyncio
    async def test_on_response_save_all_appends(self):
        crawler = _make_crawler(url_regexes=["api/data"], url_regexes_save_all=True)
        dl = _ConcreteBrowserDownloader(crawler)

        response = MagicMock()
        response.request.url = "http://example.com/api/data?page=1"
        response.request.headers = {}
        response.request.post_data_buffer = None
        response.url = "http://example.com/api/data?page=1"
        response.headers = {}
        response.body = AsyncMock(return_value=b"resp1")
        response.status = 200

        await dl.on_response(response)
        response.body = AsyncMock(return_value=b"resp2")
        await dl.on_response(response)
        assert len(dl._cache_data["api/data"]) == 2

    @pytest.mark.asyncio
    async def test_on_response_no_match(self):
        crawler = _make_crawler(url_regexes=["api/data"])
        dl = _ConcreteBrowserDownloader(crawler)

        response = MagicMock()
        response.request.url = "http://example.com/other"
        await dl.on_response(response)
        assert dl._cache_data == {}


# --- handle_download ---


class TestHandleDownload:
    @pytest.mark.asyncio
    async def test_handle_download(self, tmp_path):
        crawler = _make_crawler()
        dl = _ConcreteBrowserDownloader(crawler)

        download = MagicMock()
        download.path = AsyncMock(return_value=tmp_path / "temp_file.tmp")
        download.suggested_filename = "report.pdf"
        download.save_as = AsyncMock()

        # 创建临时文件模拟
        temp_file = tmp_path / "temp_file.tmp"
        temp_file.write_text("data")

        await dl.handle_download(download)
        download.save_as.assert_called_once_with(tmp_path / "report.pdf")
        assert not temp_file.exists()

    @pytest.mark.asyncio
    async def test_handle_download_no_original_file(self, tmp_path):
        crawler = _make_crawler()
        dl = _ConcreteBrowserDownloader(crawler)

        download = MagicMock()
        download.path = AsyncMock(return_value=tmp_path / "nonexistent.tmp")
        download.suggested_filename = "report.pdf"
        download.save_as = AsyncMock()

        await dl.handle_download(download)
        download.save_as.assert_called_once()


# --- close ---


class TestClose:
    @pytest.mark.asyncio
    async def test_close_all_resources(self):
        crawler = _make_crawler()
        dl = _ConcreteBrowserDownloader(crawler)

        mock_pool = MagicMock()
        mock_pool.close_all = AsyncMock()
        mock_context = MagicMock()
        mock_context.close = AsyncMock()
        mock_browser = MagicMock()
        mock_browser.close = AsyncMock()
        mock_pw = MagicMock()
        mock_pw.stop = AsyncMock()

        dl.page_pool = mock_pool
        dl.context = mock_context
        dl.browser = mock_browser
        dl.playwright = mock_pw

        with patch("maize.aio.classic.downloader.base_browser_downloader.BaseDownloader.close", new_callable=AsyncMock):
            await dl.close()

        mock_pool.close_all.assert_called_once()
        mock_context.close.assert_called_once()
        mock_browser.close.assert_called_once()
        mock_pw.stop.assert_called_once()
        assert dl.page_pool is None
        assert dl.context is None
        assert dl.browser is None
        assert dl.playwright is None

    @pytest.mark.asyncio
    async def test_close_no_resources(self):
        crawler = _make_crawler()
        dl = _ConcreteBrowserDownloader(crawler)
        with patch("maize.aio.classic.downloader.base_browser_downloader.BaseDownloader.close", new_callable=AsyncMock):
            await dl.close()


# --- download (session mode) ---


class TestDownloadSession:
    @pytest.mark.asyncio
    async def test_download_session_success(self):
        crawler = _make_crawler()
        crawler.settings.request.use_session = True
        dl = _ConcreteBrowserDownloader(crawler)
        dl._use_session = True
        dl._timeout = 30000

        fake_page = MagicMock()
        fake_page.goto = AsyncMock()
        fake_page.content = AsyncMock(return_value="<html>hello</html>")
        fake_page.is_closed = MagicMock(return_value=False)
        fake_page.on = MagicMock()

        fake_context = MagicMock()
        fake_context.cookies = AsyncMock(return_value=[])
        dl.context = fake_context

        dl.page_pool = MagicMock()
        dl.page_pool.acquire_page = AsyncMock(return_value=fake_page)
        dl.page_pool.release_page = AsyncMock()

        request = Request("http://example.com")
        result = await dl.download(request)
        assert isinstance(result, DownloadResponse)
        assert result.response.text == "<html>hello</html>"

    @pytest.mark.asyncio
    async def test_download_session_with_cookies(self):
        crawler = _make_crawler()
        crawler.settings.request.use_session = True
        dl = _ConcreteBrowserDownloader(crawler)
        dl._use_session = True
        dl._timeout = 30000

        fake_page = MagicMock()
        fake_page.goto = AsyncMock()
        fake_page.content = AsyncMock(return_value="<html></html>")
        fake_page.is_closed = MagicMock(return_value=False)
        fake_page.on = MagicMock()

        fake_context = MagicMock()
        fake_context.cookies = AsyncMock(return_value=[])
        fake_context.add_cookies = AsyncMock()
        dl.context = fake_context

        dl.page_pool = MagicMock()
        dl.page_pool.acquire_page = AsyncMock(return_value=fake_page)
        dl.page_pool.release_page = AsyncMock()

        request = Request("http://example.com", cookies=[{"name": "a", "value": "b"}])
        await dl.download(request)
        fake_context.add_cookies.assert_called_once()

    @pytest.mark.asyncio
    async def test_download_session_navigation_error(self):
        crawler = _make_crawler()
        crawler.settings.request.use_session = True
        dl = _ConcreteBrowserDownloader(crawler)
        dl._use_session = True
        dl._timeout = 30000

        fake_page = MagicMock()
        fake_page.goto = AsyncMock(side_effect=Exception("timeout"))
        fake_page.is_closed = MagicMock(return_value=False)
        fake_page.on = MagicMock()

        fake_context = MagicMock()
        dl.context = fake_context

        dl.page_pool = MagicMock()
        dl.page_pool.acquire_page = AsyncMock(return_value=fake_page)
        dl.page_pool.release_page = AsyncMock()

        request = Request("http://example.com")
        result = await dl.download(request)
        assert isinstance(result, DownloadResponse)
        assert result.reason == "timeout"

    @pytest.mark.asyncio
    async def test_download_session_page_state_check_error(self):
        crawler = _make_crawler()
        crawler.settings.request.use_session = True
        dl = _ConcreteBrowserDownloader(crawler)
        dl._use_session = True
        dl._timeout = 30000

        fake_page = MagicMock()
        fake_page.goto = AsyncMock(side_effect=Exception("nav error"))
        fake_page.is_closed = MagicMock(side_effect=Exception("page broken"))
        fake_page.on = MagicMock()

        fake_context = MagicMock()
        dl.context = fake_context

        dl.page_pool = MagicMock()
        dl.page_pool.acquire_page = AsyncMock(return_value=fake_page)
        dl.page_pool.release_page = AsyncMock()

        request = Request("http://example.com")
        result = await dl.download(request)
        assert isinstance(result, DownloadResponse)

    @pytest.mark.asyncio
    async def test_download_session_no_context_creates_one(self):
        crawler = _make_crawler()
        crawler.settings.request.use_session = True
        dl = _ConcreteBrowserDownloader(crawler)
        dl._use_session = True
        dl._timeout = 30000
        dl.context = None

        fake_page = MagicMock()
        fake_page.goto = AsyncMock()
        fake_page.content = AsyncMock(return_value="<html></html>")
        fake_page.is_closed = MagicMock(return_value=False)
        fake_page.on = MagicMock()

        fake_context = MagicMock()
        fake_context.cookies = AsyncMock(return_value=[])

        dl.page_pool = MagicMock()
        dl.page_pool.acquire_page = AsyncMock(return_value=fake_page)
        dl.page_pool.release_page = AsyncMock()

        with patch.object(dl, "_gen_context_and_page", new_callable=AsyncMock) as mock_gen:
            mock_gen.side_effect = lambda: setattr(dl, "context", fake_context)
            request = Request("http://example.com")
            result = await dl.download(request)

        assert isinstance(result, DownloadResponse)

    @pytest.mark.asyncio
    async def test_download_session_with_url_regexes(self):
        crawler = _make_crawler(url_regexes=["api/.*"])
        crawler.settings.request.use_session = True
        dl = _ConcreteBrowserDownloader(crawler)
        dl._use_session = True
        dl._timeout = 30000

        fake_page = MagicMock()
        fake_page.goto = AsyncMock()
        fake_page.content = AsyncMock(return_value="<html></html>")
        fake_page.is_closed = MagicMock(return_value=False)
        fake_page.on = MagicMock()

        fake_context = MagicMock()
        fake_context.cookies = AsyncMock(return_value=[])
        dl.context = fake_context

        dl.page_pool = MagicMock()
        dl.page_pool.acquire_page = AsyncMock(return_value=fake_page)
        dl.page_pool.release_page = AsyncMock()

        request = Request("http://example.com")
        await dl.download(request)
        # 验证 response 事件被注册
        calls = [c[0][0] for c in fake_page.on.call_args_list]
        assert "response" in calls


# --- download (non-session mode) ---


class TestDownloadNonSession:
    @pytest.mark.asyncio
    async def test_download_non_session_success(self):
        crawler = _make_crawler()
        crawler.settings.request.use_session = False
        dl = _ConcreteBrowserDownloader(crawler)
        dl._use_session = False
        dl._timeout = 30000
        dl._use_stealth_js = False

        fake_page = MagicMock()
        fake_page.goto = AsyncMock()
        fake_page.wait_for_load_state = AsyncMock()
        fake_page.content = AsyncMock(return_value="<html>non-session</html>")
        fake_page.is_closed = MagicMock(return_value=False)
        fake_page.close = AsyncMock()
        fake_page.on = MagicMock()

        fake_context = MagicMock()
        fake_context.new_page = AsyncMock(return_value=fake_page)
        fake_context.cookies = AsyncMock(return_value=[])
        fake_context.close = AsyncMock()

        fake_browser = MagicMock()
        fake_browser.new_context = AsyncMock(return_value=fake_context)

        fake_pw = MagicMock()
        fake_pw.__aenter__ = AsyncMock(return_value=fake_pw)
        fake_pw.__aexit__ = AsyncMock(return_value=False)
        dl._fake_playwright_context = fake_pw

        with patch.object(dl, "_get_browser", new_callable=AsyncMock, return_value=fake_browser):
            request = Request("http://example.com")
            result = await dl.download(request)

        assert isinstance(result, DownloadResponse)
        assert result.response.text == "<html>non-session</html>"

    @pytest.mark.asyncio
    async def test_download_non_session_with_endpoint_url(self):
        crawler = _make_crawler(endpoint_url="http://localhost:9222")
        crawler.settings.request.use_session = False
        dl = _ConcreteBrowserDownloader(crawler)
        dl._use_session = False
        dl._timeout = 30000
        dl._use_stealth_js = False

        fake_page = MagicMock()
        fake_page.goto = AsyncMock()
        fake_page.wait_for_load_state = AsyncMock()
        fake_page.content = AsyncMock(return_value="<html>cdp</html>")
        fake_page.is_closed = MagicMock(return_value=False)
        fake_page.close = AsyncMock()
        fake_page.on = MagicMock()

        fake_context = MagicMock()
        fake_context.new_page = AsyncMock(return_value=fake_page)
        fake_context.cookies = AsyncMock(return_value=[])
        # endpoint_url 模式下不关闭 context

        fake_browser = MagicMock()
        fake_browser.contexts = [fake_context]

        fake_pw = MagicMock()
        fake_pw.__aenter__ = AsyncMock(return_value=fake_pw)
        fake_pw.__aexit__ = AsyncMock(return_value=False)
        dl._fake_playwright_context = fake_pw

        with patch.object(dl, "_get_browser", new_callable=AsyncMock, return_value=fake_browser):
            request = Request("http://example.com")
            result = await dl.download(request)

        assert isinstance(result, DownloadResponse)

    @pytest.mark.asyncio
    async def test_download_non_session_with_stealth_js(self):
        crawler = _make_crawler()
        crawler.settings.request.use_session = False
        crawler.settings.rpa.use_stealth_js = True
        crawler.settings.rpa.stealth_js_path = "/fake/stealth.js"
        dl = _ConcreteBrowserDownloader(crawler)
        dl._use_session = False
        dl._timeout = 30000
        dl._use_stealth_js = True
        dl._stealth_js_path = "/fake/stealth.js"

        fake_page = MagicMock()
        fake_page.goto = AsyncMock()
        fake_page.wait_for_load_state = AsyncMock()
        fake_page.content = AsyncMock(return_value="<html></html>")
        fake_page.is_closed = MagicMock(return_value=False)
        fake_page.close = AsyncMock()
        fake_page.on = MagicMock()

        fake_context = MagicMock()
        fake_context.new_page = AsyncMock(return_value=fake_page)
        fake_context.cookies = AsyncMock(return_value=[])
        fake_context.close = AsyncMock()
        fake_context.add_init_script = AsyncMock()

        fake_browser = MagicMock()
        fake_browser.new_context = AsyncMock(return_value=fake_context)

        fake_pw = MagicMock()
        fake_pw.__aenter__ = AsyncMock(return_value=fake_pw)
        fake_pw.__aexit__ = AsyncMock(return_value=False)
        dl._fake_playwright_context = fake_pw

        with patch.object(dl, "_get_browser", new_callable=AsyncMock, return_value=fake_browser):
            request = Request("http://example.com")
            await dl.download(request)

        fake_context.add_init_script.assert_called_once_with(path="/fake/stealth.js")

    @pytest.mark.asyncio
    async def test_download_non_session_with_skip_resource_types(self):
        crawler = _make_crawler(skip_resource_types=["image", "font"])
        crawler.settings.request.use_session = False
        dl = _ConcreteBrowserDownloader(crawler)
        dl._use_session = False
        dl._timeout = 30000
        dl._use_stealth_js = False

        fake_page = MagicMock()
        fake_page.goto = AsyncMock()
        fake_page.wait_for_load_state = AsyncMock()
        fake_page.content = AsyncMock(return_value="<html></html>")
        fake_page.is_closed = MagicMock(return_value=False)
        fake_page.close = AsyncMock()
        fake_page.on = MagicMock()

        fake_context = MagicMock()
        fake_context.new_page = AsyncMock(return_value=fake_page)
        fake_context.cookies = AsyncMock(return_value=[])
        fake_context.close = AsyncMock()
        fake_context.route = MagicMock(return_value=None)  # 同步返回

        fake_browser = MagicMock()
        fake_browser.new_context = AsyncMock(return_value=fake_context)

        fake_pw = MagicMock()
        fake_pw.__aenter__ = AsyncMock(return_value=fake_pw)
        fake_pw.__aexit__ = AsyncMock(return_value=False)
        dl._fake_playwright_context = fake_pw

        with patch.object(dl, "_get_browser", new_callable=AsyncMock, return_value=fake_browser):
            request = Request("http://example.com")
            await dl.download(request)

        fake_context.route.assert_called_once()

    @pytest.mark.asyncio
    async def test_download_non_session_route_returns_coroutine(self):
        crawler = _make_crawler(skip_resource_types=["image"])
        crawler.settings.request.use_session = False
        dl = _ConcreteBrowserDownloader(crawler)
        dl._use_session = False
        dl._timeout = 30000
        dl._use_stealth_js = False

        fake_page = MagicMock()
        fake_page.goto = AsyncMock()
        fake_page.wait_for_load_state = AsyncMock()
        fake_page.content = AsyncMock(return_value="<html></html>")
        fake_page.is_closed = MagicMock(return_value=False)
        fake_page.close = AsyncMock()
        fake_page.on = MagicMock()

        async def _fake_route(*args):
            pass

        fake_context = MagicMock()
        fake_context.new_page = AsyncMock(return_value=fake_page)
        fake_context.cookies = AsyncMock(return_value=[])
        fake_context.close = AsyncMock()
        fake_context.route = MagicMock(return_value=_fake_route())

        fake_browser = MagicMock()
        fake_browser.new_context = AsyncMock(return_value=fake_context)

        fake_pw = MagicMock()
        fake_pw.__aenter__ = AsyncMock(return_value=fake_pw)
        fake_pw.__aexit__ = AsyncMock(return_value=False)
        dl._fake_playwright_context = fake_pw

        with patch.object(dl, "_get_browser", new_callable=AsyncMock, return_value=fake_browser):
            request = Request("http://example.com")
            await dl.download(request)

    @pytest.mark.asyncio
    async def test_download_non_session_route_error_ignored(self):
        crawler = _make_crawler(skip_resource_types=["image"])
        crawler.settings.request.use_session = False
        dl = _ConcreteBrowserDownloader(crawler)
        dl._use_session = False
        dl._timeout = 30000
        dl._use_stealth_js = False

        fake_page = MagicMock()
        fake_page.goto = AsyncMock()
        fake_page.wait_for_load_state = AsyncMock()
        fake_page.content = AsyncMock(return_value="<html></html>")
        fake_page.is_closed = MagicMock(return_value=False)
        fake_page.close = AsyncMock()
        fake_page.on = MagicMock()

        fake_context = MagicMock()
        fake_context.new_page = AsyncMock(return_value=fake_page)
        fake_context.cookies = AsyncMock(return_value=[])
        fake_context.close = AsyncMock()
        fake_context.route = MagicMock(side_effect=Exception("route not supported"))

        fake_browser = MagicMock()
        fake_browser.new_context = AsyncMock(return_value=fake_context)

        fake_pw = MagicMock()
        fake_pw.__aenter__ = AsyncMock(return_value=fake_pw)
        fake_pw.__aexit__ = AsyncMock(return_value=False)
        dl._fake_playwright_context = fake_pw

        with patch.object(dl, "_get_browser", new_callable=AsyncMock, return_value=fake_browser):
            request = Request("http://example.com")
            result = await dl.download(request)

        assert isinstance(result, DownloadResponse)

    @pytest.mark.asyncio
    async def test_download_non_session_page_close_error(self):
        crawler = _make_crawler()
        crawler.settings.request.use_session = False
        dl = _ConcreteBrowserDownloader(crawler)
        dl._use_session = False
        dl._timeout = 30000
        dl._use_stealth_js = False

        fake_page = MagicMock()
        fake_page.goto = AsyncMock()
        fake_page.wait_for_load_state = AsyncMock()
        fake_page.content = AsyncMock(return_value="<html></html>")
        fake_page.is_closed = MagicMock(return_value=False)
        fake_page.close = AsyncMock(side_effect=Exception("close error"))
        fake_page.on = MagicMock()

        fake_context = MagicMock()
        fake_context.new_page = AsyncMock(return_value=fake_page)
        fake_context.cookies = AsyncMock(return_value=[])
        fake_context.close = AsyncMock(side_effect=Exception("ctx close error"))

        fake_browser = MagicMock()
        fake_browser.new_context = AsyncMock(return_value=fake_context)

        fake_pw = MagicMock()
        fake_pw.__aenter__ = AsyncMock(return_value=fake_pw)
        fake_pw.__aexit__ = AsyncMock(return_value=False)
        dl._fake_playwright_context = fake_pw

        with patch.object(dl, "_get_browser", new_callable=AsyncMock, return_value=fake_browser):
            request = Request("http://example.com")
            result = await dl.download(request)

        assert isinstance(result, DownloadResponse)

    @pytest.mark.asyncio
    async def test_download_non_session_with_proxy(self):
        crawler = _make_crawler()
        crawler.settings.request.use_session = False
        crawler.settings.proxy.proxy_url = "http://127.0.0.1:8080"
        dl = _ConcreteBrowserDownloader(crawler)
        dl._use_session = False
        dl._timeout = 30000
        dl._use_stealth_js = False

        fake_page = MagicMock()
        fake_page.goto = AsyncMock()
        fake_page.wait_for_load_state = AsyncMock()
        fake_page.content = AsyncMock(return_value="<html></html>")
        fake_page.is_closed = MagicMock(return_value=False)
        fake_page.close = AsyncMock()
        fake_page.on = MagicMock()

        fake_context = MagicMock()
        fake_context.new_page = AsyncMock(return_value=fake_page)
        fake_context.cookies = AsyncMock(return_value=[])
        fake_context.close = AsyncMock()

        fake_browser = MagicMock()
        fake_browser.new_context = AsyncMock(return_value=fake_context)

        fake_pw = MagicMock()
        fake_pw.__aenter__ = AsyncMock(return_value=fake_pw)
        fake_pw.__aexit__ = AsyncMock(return_value=False)
        dl._fake_playwright_context = fake_pw

        with patch.object(dl, "_get_browser", new_callable=AsyncMock, return_value=fake_browser):
            request = Request("http://example.com")
            await dl.download(request)

        # 验证 proxy 被传入 context_kwargs
        call_kwargs = fake_browser.new_context.call_args[1]
        assert "proxy" in call_kwargs


# --- structure_response ---


class TestStructureResponse:
    def test_structure_response_with_cookies(self):
        crawler = _make_crawler()
        dl = _ConcreteBrowserDownloader(crawler)
        request = Request("http://example.com")
        cookies = [
            {
                "name": "session",
                "value": "abc123",
                "domain": ".example.com",
                "path": "/",
                "expires": 1700000000,
                "secure": True,
                "httpOnly": True,
            }
        ]
        result = dl.structure_response(request, "<html>test</html>", cookies)
        assert isinstance(result, DownloadResponse)
        assert result.response.text == "<html>test</html>"
        assert result.response.url == "http://example.com"

    def test_structure_response_no_cookies(self):
        crawler = _make_crawler()
        dl = _ConcreteBrowserDownloader(crawler)
        request = Request("http://example.com")
        result = dl.structure_response(request, "<html></html>", [])
        assert isinstance(result, DownloadResponse)


# --- _get_proxy_config ---


class TestGetProxyConfig:
    def test_no_proxy(self):
        crawler = _make_crawler()
        dl = _ConcreteBrowserDownloader(crawler)
        assert dl._get_proxy_config() is None

    def test_proxy_without_scheme(self):
        crawler = _make_crawler()
        crawler.settings.proxy.proxy_url = "127.0.0.1:8080"
        dl = _ConcreteBrowserDownloader(crawler)
        config = dl._get_proxy_config()
        assert config["server"] == "http://127.0.0.1:8080"

    def test_proxy_with_scheme(self):
        crawler = _make_crawler()
        crawler.settings.proxy.proxy_url = "socks5://127.0.0.1:1080"
        dl = _ConcreteBrowserDownloader(crawler)
        config = dl._get_proxy_config()
        assert config["server"] == "socks5://127.0.0.1:1080"

    def test_proxy_with_auth(self):
        crawler = _make_crawler()
        crawler.settings.proxy.proxy_url = "http://127.0.0.1:8080"
        crawler.settings.proxy.proxy_username = "user"
        crawler.settings.proxy.proxy_password = "pass"
        dl = _ConcreteBrowserDownloader(crawler)
        config = dl._get_proxy_config()
        assert config["username"] == "user"
        assert config["password"] == "pass"


# --- _get_browser ---


class TestGetBrowser:
    @pytest.mark.asyncio
    async def test_get_browser_launch(self):
        crawler = _make_crawler()
        dl = _ConcreteBrowserDownloader(crawler)
        dl._timeout = 30000

        fake_playwright = MagicMock()
        fake_driver = MagicMock()
        fake_driver.launch = AsyncMock(return_value="browser_instance")
        setattr(fake_playwright, dl._BaseBrowserDownloader__rpa_driver_type, fake_driver)

        result = await dl._get_browser(fake_playwright)
        assert result == "browser_instance"
        fake_driver.launch.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_browser_connect_over_cdp(self):
        crawler = _make_crawler(endpoint_url="http://localhost:9222")
        dl = _ConcreteBrowserDownloader(crawler)
        dl._timeout = 30000

        fake_playwright = MagicMock()
        fake_driver = MagicMock()
        fake_driver.connect_over_cdp = AsyncMock(return_value="cdp_browser")
        setattr(fake_playwright, dl._BaseBrowserDownloader__rpa_driver_type, fake_driver)

        result = await dl._get_browser(fake_playwright)
        assert result == "cdp_browser"
        fake_driver.connect_over_cdp.assert_called_once()


# --- _gen_context_and_page ---


class TestGenContextAndPage:
    @pytest.mark.asyncio
    async def test_gen_context_endpoint_url(self):
        crawler = _make_crawler(endpoint_url="http://localhost:9222")
        dl = _ConcreteBrowserDownloader(crawler)
        fake_context = MagicMock()
        dl.browser = MagicMock()
        dl.browser.contexts = [fake_context]

        await dl._gen_context_and_page()
        assert dl.context is fake_context

    @pytest.mark.asyncio
    async def test_gen_context_endpoint_url_with_proxy_warning(self):
        crawler = _make_crawler(endpoint_url="http://localhost:9222")
        crawler.settings.proxy.proxy_url = "http://127.0.0.1:8080"
        dl = _ConcreteBrowserDownloader(crawler)
        fake_context = MagicMock()
        dl.browser = MagicMock()
        dl.browser.contexts = [fake_context]

        await dl._gen_context_and_page()
        assert dl.context is fake_context

    @pytest.mark.asyncio
    async def test_gen_context_new_context(self):
        crawler = _make_crawler()
        dl = _ConcreteBrowserDownloader(crawler)
        dl._use_stealth_js = False
        dl._stealth_js_path = None

        fake_context = MagicMock()
        dl.browser = MagicMock()
        dl.browser.new_context = AsyncMock(return_value=fake_context)

        await dl._gen_context_and_page()
        assert dl.context is fake_context

    @pytest.mark.asyncio
    async def test_gen_context_with_stealth(self):
        crawler = _make_crawler()
        dl = _ConcreteBrowserDownloader(crawler)
        dl._use_stealth_js = True
        dl._stealth_js_path = "/stealth.js"

        fake_context = MagicMock()
        fake_context.add_init_script = AsyncMock()
        dl.browser = MagicMock()
        dl.browser.new_context = AsyncMock(return_value=fake_context)

        await dl._gen_context_and_page()
        fake_context.add_init_script.assert_called_once_with(path="/stealth.js")

    @pytest.mark.asyncio
    async def test_gen_context_with_skip_resource_types(self):
        crawler = _make_crawler(skip_resource_types=["image"])
        dl = _ConcreteBrowserDownloader(crawler)
        dl._use_stealth_js = False
        dl._stealth_js_path = None
        dl._context_route_initialized = False

        fake_context = MagicMock()
        fake_context.route = MagicMock(return_value=None)
        dl.browser = MagicMock()
        dl.browser.new_context = AsyncMock(return_value=fake_context)

        await dl._gen_context_and_page()
        assert dl._context_route_initialized is True

    @pytest.mark.asyncio
    async def test_gen_context_route_error_ignored(self):
        crawler = _make_crawler(skip_resource_types=["image"])
        dl = _ConcreteBrowserDownloader(crawler)
        dl._use_stealth_js = False
        dl._stealth_js_path = None
        dl._context_route_initialized = False

        fake_context = MagicMock()
        fake_context.route = MagicMock(side_effect=Exception("not supported"))
        dl.browser = MagicMock()
        dl.browser.new_context = AsyncMock(return_value=fake_context)

        await dl._gen_context_and_page()
        assert dl._context_route_initialized is False

    @pytest.mark.asyncio
    async def test_gen_context_with_proxy(self):
        crawler = _make_crawler()
        crawler.settings.proxy.proxy_url = "http://127.0.0.1:8080"
        dl = _ConcreteBrowserDownloader(crawler)
        dl._use_stealth_js = False
        dl._stealth_js_path = None

        fake_context = MagicMock()
        dl.browser = MagicMock()
        dl.browser.new_context = AsyncMock(return_value=fake_context)

        await dl._gen_context_and_page()
        call_kwargs = dl.browser.new_context.call_args[1]
        assert "proxy" in call_kwargs


# --- cache methods ---


class TestCacheMethods:
    def _setup_cache(self, dl):
        req = InterceptRequest(url="http://x.com", headers={}, data=None)
        resp1 = InterceptResponse(request=req, url="http://x.com", headers={}, content=b'{"a": 1}', status_code=200)
        resp2 = InterceptResponse(request=req, url="http://x.com", headers={}, content=b'{"b": 2}', status_code=200)
        dl._cache_data = {"api/.*": [resp1, resp2]}

    def test_get_response(self):
        crawler = _make_crawler()
        dl = _ConcreteBrowserDownloader(crawler)
        self._setup_cache(dl)
        resp = dl.get_response("api/.*")
        assert resp is not None
        assert resp.content == b'{"a": 1}'

    def test_get_response_none(self):
        crawler = _make_crawler()
        dl = _ConcreteBrowserDownloader(crawler)
        assert dl.get_response("nonexistent") is None

    def test_get_all_response(self):
        crawler = _make_crawler()
        dl = _ConcreteBrowserDownloader(crawler)
        self._setup_cache(dl)
        assert len(dl.get_all_response("api/.*")) == 2

    def test_get_all_response_empty(self):
        crawler = _make_crawler()
        dl = _ConcreteBrowserDownloader(crawler)
        assert dl.get_all_response("nonexistent") == []

    def test_get_text(self):
        crawler = _make_crawler()
        dl = _ConcreteBrowserDownloader(crawler)
        self._setup_cache(dl)
        assert dl.get_text("api/.*") == '{"a": 1}'

    def test_get_text_none(self):
        crawler = _make_crawler()
        dl = _ConcreteBrowserDownloader(crawler)
        assert dl.get_text("nonexistent") is None

    def test_get_all_text(self):
        crawler = _make_crawler()
        dl = _ConcreteBrowserDownloader(crawler)
        self._setup_cache(dl)
        texts = dl.get_all_text("api/.*")
        assert texts == ['{"a": 1}', '{"b": 2}']

    def test_get_json(self):
        crawler = _make_crawler()
        dl = _ConcreteBrowserDownloader(crawler)
        self._setup_cache(dl)
        assert dl.get_json("api/.*") == {"a": 1}

    def test_get_json_none(self):
        crawler = _make_crawler()
        dl = _ConcreteBrowserDownloader(crawler)
        assert dl.get_json("nonexistent") is None

    def test_get_all_json(self):
        crawler = _make_crawler()
        dl = _ConcreteBrowserDownloader(crawler)
        self._setup_cache(dl)
        assert dl.get_all_json("api/.*") == [{"a": 1}, {"b": 2}]

    def test_clear_cache(self):
        crawler = _make_crawler()
        dl = _ConcreteBrowserDownloader(crawler)
        self._setup_cache(dl)
        dl.clear_cache()
        assert dl.get_all_response("api/.*") == []


# --- PageOperationContext ---


class TestPageOperationContext:
    @pytest.mark.asyncio
    async def test_get_page_context(self):
        crawler = _make_crawler()
        dl = _ConcreteBrowserDownloader(crawler)

        fake_page = MagicMock()
        fake_context = MagicMock()
        dl.context = fake_context
        dl.page_pool = MagicMock()
        dl.page_pool.acquire_page = AsyncMock(return_value=fake_page)
        dl.page_pool.release_page = AsyncMock()

        async with dl.get_page() as page:
            assert page is fake_page

        dl.page_pool.release_page.assert_called_once_with(fake_page)

    @pytest.mark.asyncio
    async def test_get_page_context_creates_context(self):
        crawler = _make_crawler()
        dl = _ConcreteBrowserDownloader(crawler)
        dl.context = None

        fake_page = MagicMock()
        fake_context = MagicMock()
        dl.page_pool = MagicMock()
        dl.page_pool.acquire_page = AsyncMock(return_value=fake_page)
        dl.page_pool.release_page = AsyncMock()

        with patch.object(dl, "_gen_context_and_page", new_callable=AsyncMock) as mock_gen:
            mock_gen.side_effect = lambda: setattr(dl, "context", fake_context)
            async with dl.get_page() as page:
                assert page is fake_page


# --- _route_handler ---


class TestRouteHandler:
    @pytest.mark.asyncio
    async def test_route_handler_skip_url_pattern(self):
        crawler = _make_crawler(skip_url_patterns=["ads\\.js"])
        dl = _ConcreteBrowserDownloader(crawler)

        route = MagicMock()
        route.abort = AsyncMock()
        request = MagicMock()
        request.url = "http://example.com/ads.js"

        await dl._route_handler(route, request)
        route.abort.assert_called_once()

    @pytest.mark.asyncio
    async def test_route_handler_skip_resource_type(self):
        crawler = _make_crawler(skip_resource_types=["image"])
        dl = _ConcreteBrowserDownloader(crawler)

        route = MagicMock()
        route.abort = AsyncMock()
        request = MagicMock()
        request.url = "http://example.com/logo.png"
        request.resource_type = "image"

        await dl._route_handler(route, request)
        route.abort.assert_called_once()

    @pytest.mark.asyncio
    async def test_route_handler_continue(self):
        crawler = _make_crawler(skip_resource_types=["image"])
        dl = _ConcreteBrowserDownloader(crawler)

        route = MagicMock()
        route.continue_ = AsyncMock()
        request = MagicMock()
        request.url = "http://example.com/api/data"
        request.resource_type = "xhr"

        await dl._route_handler(route, request)
        route.continue_.assert_called_once()

    @pytest.mark.asyncio
    async def test_route_handler_abort_error(self):
        crawler = _make_crawler(skip_url_patterns=["ads\\.js"])
        dl = _ConcreteBrowserDownloader(crawler)

        route = MagicMock()
        route.abort = AsyncMock(side_effect=Exception("abort failed"))
        route.continue_ = AsyncMock()
        request = MagicMock()
        request.url = "http://example.com/ads.js"

        await dl._route_handler(route, request)
        # abort 失败后继续 continue
        route.continue_.assert_called_once()

    @pytest.mark.asyncio
    async def test_route_handler_continue_error(self):
        crawler = _make_crawler()
        dl = _ConcreteBrowserDownloader(crawler)

        route = MagicMock()
        route.continue_ = AsyncMock(side_effect=Exception("continue failed"))
        request = MagicMock()
        request.url = "http://example.com/page"
        request.resource_type = None

        # 不应抛出异常
        await dl._route_handler(route, request)

    @pytest.mark.asyncio
    async def test_route_handler_resource_type_uppercase(self):
        crawler = _make_crawler(skip_resource_types=["Image"])
        dl = _ConcreteBrowserDownloader(crawler)

        route = MagicMock()
        route.abort = AsyncMock()
        request = MagicMock()
        request.url = "http://example.com/logo.png"
        request.resource_type = "image"

        await dl._route_handler(route, request)
        route.abort.assert_called_once()


# --- Additional edge cases for remaining uncovered lines ---


class TestDownloadNonSessionEdgeCases:
    @pytest.mark.asyncio
    async def test_download_non_session_endpoint_with_proxy_warning(self):
        """覆盖 line 297: endpoint_url + proxy 时的 warning 分支。"""
        crawler = _make_crawler(endpoint_url="http://localhost:9222")
        crawler.settings.request.use_session = False
        crawler.settings.proxy.proxy_url = "http://127.0.0.1:8080"
        dl = _ConcreteBrowserDownloader(crawler)
        dl._use_session = False
        dl._timeout = 30000
        dl._use_stealth_js = False

        fake_page = MagicMock()
        fake_page.goto = AsyncMock()
        fake_page.wait_for_load_state = AsyncMock()
        fake_page.content = AsyncMock(return_value="<html></html>")
        fake_page.is_closed = MagicMock(return_value=False)
        fake_page.close = AsyncMock()
        fake_page.on = MagicMock()

        fake_context = MagicMock()
        fake_context.new_page = AsyncMock(return_value=fake_page)
        fake_context.cookies = AsyncMock(return_value=[])

        fake_browser = MagicMock()
        fake_browser.contexts = [fake_context]

        fake_pw = MagicMock()
        fake_pw.__aenter__ = AsyncMock(return_value=fake_pw)
        fake_pw.__aexit__ = AsyncMock(return_value=False)
        dl._fake_playwright_context = fake_pw

        with patch.object(dl, "_get_browser", new_callable=AsyncMock, return_value=fake_browser):
            request = Request("http://example.com")
            result = await dl.download(request)

        assert isinstance(result, DownloadResponse)

    @pytest.mark.asyncio
    async def test_download_non_session_with_cookies(self):
        """覆盖 line 316: 非 session 模式下 request.cookies 分支。"""
        crawler = _make_crawler()
        crawler.settings.request.use_session = False
        dl = _ConcreteBrowserDownloader(crawler)
        dl._use_session = False
        dl._timeout = 30000
        dl._use_stealth_js = False

        fake_page = MagicMock()
        fake_page.goto = AsyncMock()
        fake_page.wait_for_load_state = AsyncMock()
        fake_page.content = AsyncMock(return_value="<html></html>")
        fake_page.is_closed = MagicMock(return_value=False)
        fake_page.close = AsyncMock()
        fake_page.on = MagicMock()

        fake_context = MagicMock()
        fake_context.new_page = AsyncMock(return_value=fake_page)
        fake_context.cookies = AsyncMock(return_value=[])
        fake_context.close = AsyncMock()
        fake_context.add_cookies = AsyncMock()

        fake_browser = MagicMock()
        fake_browser.new_context = AsyncMock(return_value=fake_context)

        fake_pw = MagicMock()
        fake_pw.__aenter__ = AsyncMock(return_value=fake_pw)
        fake_pw.__aexit__ = AsyncMock(return_value=False)
        dl._fake_playwright_context = fake_pw

        with patch.object(dl, "_get_browser", new_callable=AsyncMock, return_value=fake_browser):
            request = Request("http://example.com", cookies=[{"name": "sid", "value": "x"}])
            await dl.download(request)

        fake_context.add_cookies.assert_called_once()

    @pytest.mark.asyncio
    async def test_download_retry_returns_request(self):
        """覆盖 line 346: _download_retry 返回 Request 的重试路径。"""
        crawler = _make_crawler()
        crawler.settings.request.use_session = False
        crawler.settings.request.max_retry_count = 3
        dl = _ConcreteBrowserDownloader(crawler)
        dl._use_session = False
        dl._timeout = 30000
        dl._use_stealth_js = False

        fake_page = MagicMock()
        fake_page.goto = AsyncMock(side_effect=Exception("timeout"))
        fake_page.is_closed = MagicMock(return_value=False)
        fake_page.close = AsyncMock()
        fake_page.on = MagicMock()

        fake_context = MagicMock()
        fake_context.new_page = AsyncMock(return_value=fake_page)
        fake_context.close = AsyncMock()

        fake_browser = MagicMock()
        fake_browser.new_context = AsyncMock(return_value=fake_context)

        fake_pw = MagicMock()
        fake_pw.__aenter__ = AsyncMock(return_value=fake_pw)
        fake_pw.__aexit__ = AsyncMock(return_value=False)
        dl._fake_playwright_context = fake_pw

        request = Request("http://example.com")

        with patch.object(dl, "_get_browser", new_callable=AsyncMock, return_value=fake_browser):
            result = await dl.download(request)

        # 重试时返回 Request 对象
        assert isinstance(result, Request)


class TestGenContextRouteCoroutine:
    @pytest.mark.asyncio
    async def test_gen_context_route_returns_coroutine(self):
        """覆盖 line 468: _gen_context_and_page 中 route 返回 coroutine 的分支。"""
        crawler = _make_crawler(skip_resource_types=["image"])
        dl = _ConcreteBrowserDownloader(crawler)
        dl._use_stealth_js = False
        dl._stealth_js_path = None
        dl._context_route_initialized = False

        async def _fake_route(*args):
            pass

        fake_context = MagicMock()
        fake_context.route = MagicMock(return_value=_fake_route())
        dl.browser = MagicMock()
        dl.browser.new_context = AsyncMock(return_value=fake_context)

        await dl._gen_context_and_page()
        assert dl._context_route_initialized is True


class TestRouteHandlerEdgeCases:
    @pytest.mark.asyncio
    async def test_route_handler_resource_type_abort_error(self):
        """覆盖 lines 562-563: resource_type abort 失败的分支。"""
        crawler = _make_crawler(skip_resource_types=["image"])
        dl = _ConcreteBrowserDownloader(crawler)

        route = MagicMock()
        route.abort = AsyncMock(side_effect=Exception("abort failed"))
        route.continue_ = AsyncMock()
        request = MagicMock()
        request.url = "http://example.com/logo.png"
        request.resource_type = "image"

        await dl._route_handler(route, request)
        # abort 失败后继续 continue
        route.continue_.assert_called_once()

    @pytest.mark.asyncio
    async def test_route_handler_outer_exception(self):
        """覆盖 lines 569-570: 路由处理器外层异常捕获。"""
        crawler = _make_crawler()
        dl = _ConcreteBrowserDownloader(crawler)

        route = MagicMock()
        # 让 request.url 属性访问抛出异常
        request = MagicMock()
        type(request).url = property(lambda _: (_ for _ in ()).throw(RuntimeError("boom")))

        # 不应抛出异常
        await dl._route_handler(route, request)
