import asyncio
from pathlib import Path
from typing import TYPE_CHECKING
from typing import List
from typing import Optional

from playwright.async_api import Browser
from playwright.async_api import BrowserContext
from playwright.async_api import Cookie
from playwright.async_api import Download
from playwright.async_api import Page
from playwright.async_api import Playwright
from playwright.async_api import ViewportSize
from playwright.async_api import async_playwright

from maize import BaseDownloader
from maize import Request
from maize import Response


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
        self.__view_size: Optional[ViewportSize] = None

    async def open(self):
        await super().open()

        self._timeout = self.crawler.settings.REQUEST_TIMEOUT * 1000
        self._use_session = self.crawler.settings.USE_SESSION

        self._use_stealth_js = self.crawler.settings.RPA_USE_STEALTH_JS
        self._stealth_js_path = self.crawler.settings.RPA_STEALTH_JS_PATH

        self.__view_size = ViewportSize(
            width=self.__rpa_window_size[0], height=self.__rpa_window_size[1]
        )

        if self._use_session:
            self.playwright = await async_playwright().start()
            self.browser: Browser = await self.__get_browser(self.playwright)

            self.context = await self.browser.new_context(
                user_agent=self.__rpa_user_agent,
                screen=self.__view_size,
                viewport=self.__view_size,
            )
            if self._use_stealth_js:
                await self.context.add_init_script(path=self._stealth_js_path)
            self.page = await self.context.new_page()
            self.page.on("download", self.handle_download)

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

    async def download(self, request: Request) -> Optional[Response[Page]]:
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
    ) -> Response:
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
        return Response(
            url=request.url,
            headers={},
            text=response,
            request=request,
            cookie_list=cookie_list,
            driver=self.page,
        )

    async def __get_browser(self, playwright: Playwright) -> Browser:
        """
        获取 browser 实例

        @param playwright:
        @return:
        """
        if self.__rpa_endpoint_url:
            browser = await getattr(
                playwright, self.__rpa_driver_type
            ).connect_over_cdp(
                endpoint_url=self.__rpa_endpoint_url,
                timeout=self._timeout,
                slow_mo=self.__rpa_slow_mo,
                headers=self.__rpa_user_agent,
            )
        else:
            browser: Browser = await getattr(playwright, self.__rpa_driver_type).launch(
                timeout=self._timeout,
                headless=self.__rpa_headless,
                args=self.__rpa_custom_argument or ["--no-sandbox"],
                executable_path=self.__rpa_executable_path,
                downloads_path=self.__rpa_download_path,
            )
        return browser
