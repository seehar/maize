import typing
from playwright.async_api import async_playwright, Playwright, Browser, Page, BrowserContext, Cookie

from maize import BaseDownloader, Request, Response

if typing.TYPE_CHECKING:
    from maize.core.crawler import Crawler


class PlaywrightDownloader(BaseDownloader):

    def __init__(self, crawler: "Crawler"):
        super().__init__(crawler)
        self.playwright: typing.Optional[Playwright] = None
        self.browser: typing.Optional[Browser] = None
        self.page: typing.Optional[Page] = None
        self.context: typing.Optional[BrowserContext] = None

        self._timeout: typing.Optional[float] = None
        self._use_session: typing.Optional[bool] = None

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

    async def download(self, request: Request) -> typing.Optional[Response]:
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
    def structure_response(request: Request, response: str, cookies: list[Cookie]) -> Response:
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
            cookie_list=cookie_list
        )
