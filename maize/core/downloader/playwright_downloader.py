from typing import TYPE_CHECKING
from typing import List
from typing import Optional

from playwright.async_api import Browser
from playwright.async_api import BrowserContext
from playwright.async_api import Cookie
from playwright.async_api import Page
from playwright.async_api import Playwright
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

    async def open(self):
        await super().open()

        self._timeout = self.crawler.settings.getfloat("REQUEST_TIMEOUT") * 1000
        self._use_session = self.crawler.settings.getbool("USE_SESSION")
        self._use_session = self.crawler.settings.getbool("USE_SESSION")

        if self._use_session:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(timeout=self._timeout)
            self.context = await self.browser.new_context()
            self.page = await self.context.new_page()

    async def close(self):
        if self.page:
            await self.page.close()

        if self.browser:
            await self.browser.close()

        await super().close()

    async def download(self, request: Request) -> Optional[Response]:
        try:
            if self._use_session:
                await self.page.goto(request.url)
                await self.page.wait_for_load_state()
                response = await self.page.content()
                cookies = await self.page.context.cookies()

            else:
                async with async_playwright() as playwright:
                    browser = await playwright.chromium.launch(timeout=self._timeout)
                    context = await browser.new_context()
                    page = await context.new_page()
                    await page.goto(request.url)
                    await page.wait_for_load_state()
                    response = await page.content()
                    cookies = await self.page.context.cookies()

        except Exception as e:
            self.logger.error(f"Error during request: {e}")
            return None

        return self.structure_response(request, response, cookies)

    @staticmethod
    def structure_response(
        request: Request, response: str, cookies: List[Cookie]
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
        )
