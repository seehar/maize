import asyncio
import re
from abc import ABCMeta
from abc import abstractmethod
from collections import defaultdict
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Dict
from typing import Generic
from typing import List
from typing import Optional
from typing import TypeVar

import ujson

from maize import BaseDownloader
from maize import Request
from maize import Response
from maize.common.downloader.page_pool import PagePool
from maize.common.model.download_response_model import DownloadResponse
from maize.common.model.rpa_model import InterceptRequest
from maize.common.model.rpa_model import InterceptResponse


if TYPE_CHECKING:
    from maize.core.crawler import Crawler

# 定义泛型类型变量
PlaywrightT = TypeVar("PlaywrightT")
BrowserT = TypeVar("BrowserT")
BrowserContextT = TypeVar("BrowserContextT")
PageT = TypeVar("PageT")
ViewportSizeT = TypeVar("ViewportSizeT")
CookieT = TypeVar("CookieT")
DownloadT = TypeVar("DownloadT")
ResponseT = TypeVar("ResponseT")


class BaseBrowserDownloader(
    BaseDownloader,
    Generic[PlaywrightT, BrowserT, BrowserContextT, PageT, ViewportSizeT, CookieT, DownloadT, ResponseT],
    metaclass=ABCMeta,
):
    """Playwright/Patchright 通用基类，抽取公共逻辑"""

    def __init__(self, crawler: "Crawler"):
        super().__init__(crawler)
        self.playwright: Optional[PlaywrightT] = None
        self.browser: Optional[BrowserT] = None
        self.context: Optional[BrowserContextT] = None
        self.page_pool: Optional[PagePool] = None

        self._timeout: Optional[float] = None
        self._use_session: Optional[bool] = None

        self._use_stealth_js: Optional[bool] = None
        self._stealth_js_path: Optional[Path | str] = None
        self.__rpa_headless = self.crawler.settings.RPA_HEADLESS
        self.__rpa_driver_type = self.crawler.settings.RPA_DRIVER_TYPE
        self.__rpa_user_agent = self.crawler.settings.RPA_USER_AGENT
        self.__rpa_timeout = self.crawler.settings.REQUEST_TIMEOUT
        self.__rpa_window_size = self.crawler.settings.RPA_WINDOW_SIZE
        self.__rpa_executable_path = self.crawler.settings.RPA_EXECUTABLE_PATH
        self.__rpa_download_path = self.crawler.settings.RPA_DOWNLOAD_PATH
        self.__rpa_render_time = self.crawler.settings.RPA_RENDER_TIME or 0
        self.__rpa_custom_argument = self.crawler.settings.RPA_CUSTOM_ARGUMENT
        self.__rpa_endpoint_url = self.crawler.settings.RPA_ENDPOINT_URL
        self.__rpa_slow_mo = self.crawler.settings.RPA_SLOW_MO
        self.__rpa_url_regexes = self.crawler.settings.RPA_URL_REGEXES
        self.__rpa_url_regexes_save_all = self.crawler.settings.RPA_URL_REGEXES_SAVE_ALL
        self.__view_size: Optional[ViewportSizeT] = None
        self._cache_data: Dict[str, List[InterceptResponse]] = {}

        if self.__rpa_url_regexes_save_all and self.__rpa_url_regexes:
            self.logger.warning("获取完拦截的数据后, 请主动调用PlaywrightDriver的clear_cache()方法清空拦截的数据，否则数据会一直累加，导致内存溢出")

    @abstractmethod
    async def _get_playwright_instance(self):
        """获取 playwright 实例（子类实现，返回 async_playwright()）"""
        raise NotImplementedError

    @abstractmethod
    def _get_viewport_size_class(self):
        """获取 ViewportSize 类（子类实现）"""
        raise NotImplementedError

    async def open(self):
        await super().open()

        self._timeout = self.crawler.settings.REQUEST_TIMEOUT * 1000
        self._use_session = self.crawler.settings.USE_SESSION

        self._use_stealth_js = self.crawler.settings.RPA_USE_STEALTH_JS
        self._stealth_js_path = self.crawler.settings.RPA_STEALTH_JS_PATH

        viewport_size_class = self._get_viewport_size_class()
        self.__view_size = viewport_size_class(width=self.__rpa_window_size[0], height=self.__rpa_window_size[1])

        # 获取并发数设置，用于页面池大小
        concurrency = self.crawler.settings.CONCURRENCY or 10
        self.page_pool = PagePool(crawler=self.crawler, max_pages=concurrency)

        if self._use_session:
            playwright_context = await self._get_playwright_instance()
            self.playwright = await playwright_context.start()
            self.browser = await self._get_browser(self.playwright)
            await self._gen_context_and_page()

    async def on_response(self, response: ResponseT):
        """响应拦截处理"""
        for regex in self.__rpa_url_regexes:
            if re.search(regex, response.request.url):
                intercept_request = InterceptRequest(
                    url=response.request.url,
                    headers=response.request.headers,
                    data=response.request.post_data_buffer,
                )

                body = await response.body()
                intercept_response = InterceptResponse(
                    request=intercept_request,
                    url=response.url,
                    headers=response.headers,
                    content=body,
                    status_code=response.status,
                )
                if self.__rpa_url_regexes_save_all and regex in self._cache_data:
                    self._cache_data[regex].append(intercept_response)
                else:
                    self._cache_data[regex] = [intercept_response]

    async def handle_download(self, download: DownloadT):
        """下载处理"""
        download_path = await download.path()
        suggested_filename = download.suggested_filename
        await download.save_as(download_path.parent / suggested_filename)

        original_file_path = Path(download_path)
        if original_file_path.exists():
            original_file_path.unlink()

    async def close(self):
        """关闭资源"""
        # 关闭页面池
        if self.page_pool:
            await self.page_pool.close_all()
            self.page_pool = None

        if self.context:
            await self.context.close()
            self.context = None

        if self.browser:
            await self.browser.close()
            self.browser = None

        if self.playwright:
            await self.playwright.stop()
            self.playwright = None

        await super().close()

    async def download(self, request: Request) -> Optional[DownloadResponse]:
        """下载请求"""
        response = ""
        cookies = []
        page: Optional[PageT] = None
        context = None

        try:
            if self._use_session:
                # 使用页面池获取页面
                if not self.context:
                    await self._gen_context_and_page()

                page = await self.page_pool.acquire_page(self.context)

                # 设置下载和响应拦截（每次获取页面时重新设置）
                page.on("download", self.handle_download)
                if self.__rpa_url_regexes:
                    page.on("response", self.on_response)

                if request.cookies:
                    await self.context.add_cookies(request.cookies)

                # 添加更好的错误处理和超时控制
                try:
                    self.logger.info(f"Navigating to {request.url}")
                    await page.goto(request.url, timeout=self._timeout, wait_until="load")
                    self.logger.info(f"Navigation completed, waiting for render time: {self.__rpa_render_time}s")
                    await asyncio.sleep(self.__rpa_render_time)
                    response = await page.content()
                    cookies = await self.context.cookies()
                    self.logger.info(f"Successfully retrieved content from {request.url}")
                except Exception as e:
                    self.logger.error(f"Page navigation error for {request.url}: {e}")
                    # 检查页面状态
                    if page:
                        try:
                            page_state = "closed" if page.is_closed() else "open"
                            self.logger.info(f"Page state: {page_state}")
                        except Exception as e:
                            self.logger.info(f"Error checking page state: {e}")
                    raise

            else:
                # 非session模式，为每个请求创建独立的browser实例
                playwright_context = await self._get_playwright_instance()
                async with playwright_context as playwright:
                    browser = await self._get_browser(playwright)
                    context = await browser.new_context(
                        user_agent=self.__rpa_user_agent,
                        screen=self.__view_size,
                        viewport=self.__view_size,
                    )
                    if self._use_stealth_js:
                        await context.add_init_script(path=self._stealth_js_path)
                    if request.cookies:
                        await context.add_cookies(request.cookies)

                    page = await context.new_page()
                    page.on("download", self.handle_download)

                    await page.goto(request.url)
                    await page.wait_for_load_state()
                    await asyncio.sleep(self.__rpa_render_time)
                    response = await page.content()
                    cookies = await context.cookies()
            return self.structure_response(request, response, cookies)

        except Exception as e:
            self.logger.error(f"Error during request: {e}")
            if new_request := await self._download_retry(request, e):
                return new_request
            return None
        finally:
            # 清理资源
            if self._use_session and page:
                await self.page_pool.release_page(page)
            elif not self._use_session and context:
                try:
                    await page.close()
                    await context.close()
                except Exception as e:
                    self.logger.warning(f"Failed to close page or context: {e}")

    def structure_response(self, request: Request, response: str, cookies: List[CookieT]) -> DownloadResponse:
        """构建响应对象"""
        cookie_list = [
            {
                "name": cookie["name"],
                "value": cookie["value"],
                "domain": cookie["domain"],
                "path": cookie["path"],
                "expires": cookie["expires"],
                "secure": cookie["secure"],
                "httponly": cookie["httpOnly"],
            }
            for cookie in cookies
        ]
        response_instance = Response(
            url=request.url,
            headers={},
            text=response,
            request=request,
            cookie_list=cookie_list,
            driver=self,
            source_response=None,  # 由于使用页面池，不再有固定的page引用
        )
        download_response = DownloadResponse()
        download_response.response = response_instance
        return download_response

    async def _get_browser(self, playwright: PlaywrightT) -> BrowserT:
        """获取 browser 实例"""
        if self.__rpa_endpoint_url:
            browser = await getattr(playwright, self.__rpa_driver_type).connect_over_cdp(
                endpoint_url=self.__rpa_endpoint_url,
                timeout=self._timeout,
                slow_mo=self.__rpa_slow_mo,
                headers=self.__rpa_user_agent,
            )
        else:
            browser = await getattr(playwright, self.__rpa_driver_type).launch(
                timeout=self._timeout,
                headless=self.__rpa_headless,
                args=self.__rpa_custom_argument,
                executable_path=self.__rpa_executable_path,
                downloads_path=self.__rpa_download_path,
            )
        return browser

    async def _gen_context_and_page(self):
        """生成 context 和 page"""
        if self.__rpa_endpoint_url:
            self.context = self.browser.contexts[0]
            return

        self.context = await self.browser.new_context(
            user_agent=self.__rpa_user_agent,
            screen=self.__view_size,
            viewport=self.__view_size,
        )
        if self._use_stealth_js:
            await self.context.add_init_script(path=self._stealth_js_path)
        # 不再创建单个page，页面池会在需要时创建页面

    def get_response(self, url_regex: str) -> Optional[InterceptResponse]:
        """获取拦截的响应"""
        response_list = self._cache_data.get(url_regex)
        return response_list[0] if response_list else None

    def get_all_response(self, url_regex) -> List[InterceptResponse]:
        """获取所有拦截的响应"""
        return self._cache_data.get(url_regex, [])

    def get_text(self, url_regex: str) -> Optional[str]:
        """获取拦截响应的文本内容"""
        return self.get_response(url_regex).content.decode() if self.get_response(url_regex) else None

    def get_all_text(self, url_regex: str) -> List[str]:
        """获取所有拦截响应的文本内容"""
        return [response.content.decode() for response in self.get_all_response(url_regex)]

    def get_json(self, url_regex: str) -> Optional[dict]:
        """获取拦截响应的JSON内容"""
        text = self.get_text(url_regex)
        return ujson.loads(text) if text else None

    def get_all_json(self, url_regex: str) -> List[dict]:
        """获取所有拦截响应的JSON内容"""
        return [ujson.loads(text) for text in self.get_all_text(url_regex)]

    def clear_cache(self):
        """清空缓存"""
        self._cache_data = defaultdict(list)

    class PageOperationContext:
        """页面操作上下文管理器，确保页面正确释放"""

        def __init__(self, downloader: "BaseBrowserDownloader"):
            self.downloader = downloader
            self.page: Optional[PageT] = None

        async def __aenter__(self) -> PageT:
            """进入上下文，获取页面"""
            if not self.downloader.context:
                await self.downloader._gen_context_and_page()

            self.page = await self.downloader.page_pool.acquire_page(self.downloader.context)
            return self.page

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            """退出上下文，释放页面"""
            if self.page:
                await self.downloader.page_pool.release_page(self.page)
                self.page = None

    def get_page(self) -> "PageOperationContext":
        """
        获取页面操作上下文管理器
        使用示例：
        async with downloader.get_page() as page:
            # 在此处使用page进行操作
            await page.goto("https://example.com")
        """
        return self.PageOperationContext(self)
