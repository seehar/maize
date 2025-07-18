import asyncio
import re
from collections import defaultdict
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Dict
from typing import List
from typing import Optional

import ujson
from playwright.async_api import Browser
from playwright.async_api import BrowserContext
from playwright.async_api import Cookie
from playwright.async_api import Download
from playwright.async_api import Page
from playwright.async_api import Playwright
from playwright.async_api import Response as PlaywrightResponse
from playwright.async_api import ViewportSize
from playwright.async_api import async_playwright

from maize import BaseDownloader
from maize import Request
from maize import Response
from maize.common.model.download_response_model import DownloadResponse
from maize.common.model.rpa_model import InterceptRequest
from maize.common.model.rpa_model import InterceptResponse


if TYPE_CHECKING:
    from maize.core.crawler import Crawler


class PlaywrightDownloader(BaseDownloader):
    def __init__(self, crawler: "Crawler"):
        super().__init__(crawler)
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.context: Optional[BrowserContext] = None

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
        self.__view_size: Optional[ViewportSize] = None
        self._cache_data: Dict[str, List[InterceptResponse]] = {}

        if self.__rpa_url_regexes_save_all and self.__rpa_url_regexes:
            self.logger.warning("获取完拦截的数据后, 请主动调用PlaywrightDriver的clear_cache()方法清空拦截的数据，否则数据会一直累加，导致内存溢出")

    async def open(self):
        await super().open()

        self._timeout = self.crawler.settings.REQUEST_TIMEOUT * 1000
        self._use_session = self.crawler.settings.USE_SESSION

        self._use_stealth_js = self.crawler.settings.RPA_USE_STEALTH_JS
        self._stealth_js_path = self.crawler.settings.RPA_STEALTH_JS_PATH

        self.__view_size = ViewportSize(width=self.__rpa_window_size[0], height=self.__rpa_window_size[1])

        if self._use_session:
            self.playwright = await async_playwright().start()
            self.browser: Browser = await self.__get_browser(self.playwright)
            await self.__gen_context_and_page()
            self.page.on("download", self.handle_download)

        if self.__rpa_url_regexes:
            self.page.on("response", self.on_response)

    async def on_response(self, response: PlaywrightResponse):
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

    @staticmethod
    async def handle_download(download: Download):
        download_path = await download.path()
        suggested_filename = download.suggested_filename
        await download.save_as(download_path.parent / suggested_filename)

        original_file_path = Path(download_path)
        if original_file_path.exists():
            original_file_path.unlink()

    async def close(self):
        if self.page:
            await self.page.close()
            self.page = None

        if self.browser:
            await self.browser.close()
            self.browser = None

        if self.playwright:
            await self.playwright.stop()
            self.playwright = None

        await super().close()

    async def download(self, request: Request) -> Optional[DownloadResponse["PlaywrightDownloader", Page]]:
        response = ""
        cookies = []
        try:
            if self._use_session:
                if request.cookies:
                    await self.page.context.add_cookies(request.cookies)
                await self.page.goto(request.url)
                await asyncio.sleep(self.__rpa_render_time)
                await self.page.wait_for_load_state()
                response = await self.page.content()
                cookies = await self.page.context.cookies()

            else:
                async with async_playwright() as playwright:
                    browser = await self.__get_browser(playwright)
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
                    cookies = await page.context.cookies()

        except Exception as e:
            self.logger.error(f"Error during request: {e}")
            return None

        return self.structure_response(request, response, cookies)

    def structure_response(
        self, request: Request, response: str, cookies: List[Cookie]
    ) -> DownloadResponse["PlaywrightDownloader", Page]:
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
        response_instance = Response["PlaywrightDownloader", Page](
            url=request.url,
            headers={},
            text=response,
            request=request,
            cookie_list=cookie_list,
            driver=self,
            source_response=self.page,
        )
        download_response = DownloadResponse()
        download_response.response = response_instance
        return download_response

    async def __get_browser(self, playwright: Playwright) -> Browser:
        """
        获取 browser 实例

        @param playwright:
        @return:
        """
        if self.__rpa_endpoint_url:
            browser = await getattr(playwright, self.__rpa_driver_type).connect_over_cdp(
                endpoint_url=self.__rpa_endpoint_url,
                timeout=self._timeout,
                slow_mo=self.__rpa_slow_mo,
                headers=self.__rpa_user_agent,
            )
        else:
            browser: Browser = await getattr(playwright, self.__rpa_driver_type).launch(
                timeout=self._timeout,
                headless=self.__rpa_headless,
                args=self.__rpa_custom_argument,
                executable_path=self.__rpa_executable_path,
                downloads_path=self.__rpa_download_path,
            )
        return browser

    async def __gen_context_and_page(self):
        if self.__rpa_endpoint_url:
            self.context = self.browser.contexts[0]
            self.page = self.context.pages[0]
            return

        self.context = await self.browser.new_context(
            user_agent=self.__rpa_user_agent,
            screen=self.__view_size,
            viewport=self.__view_size,
        )
        if self._use_stealth_js:
            await self.context.add_init_script(path=self._stealth_js_path)
        self.page = await self.context.new_page()

    def get_response(self, url_regex: str) -> Optional[InterceptResponse]:
        response_list = self._cache_data.get(url_regex)
        return response_list[0] if response_list else None

    def get_all_response(self, url_regex) -> List[InterceptResponse]:
        return self._cache_data.get(url_regex, [])

    def get_text(self, url_regex: str) -> Optional[str]:
        return self.get_response(url_regex).content.decode() if self.get_response(url_regex) else None

    def get_all_text(self, url_regex: str) -> List[str]:
        return [response.content.decode() for response in self.get_all_response(url_regex)]

    def get_json(self, url_regex: str) -> Optional[dict]:
        text = self.get_text(url_regex)
        return ujson.loads(text) if text else None

    def get_all_json(self, url_regex: str) -> List[dict]:
        return [ujson.loads(text) for text in self.get_all_text(url_regex)]

    def clear_cache(self):
        self._cache_data = defaultdict(list)
