from patchright.async_api import Browser
from patchright.async_api import BrowserContext
from patchright.async_api import Cookie
from patchright.async_api import Download
from patchright.async_api import Page
from patchright.async_api import Playwright
from patchright.async_api import Response as PatchrightResponse
from patchright.async_api import ViewportSize
from patchright.async_api import async_playwright

from maize.downloader.base.base_browser_downloader import BaseBrowserDownloader


class PatchrightDownloader(
    BaseBrowserDownloader[Playwright, Browser, BrowserContext, Page, ViewportSize, Cookie, Download, PatchrightResponse]
):
    """Patchright 下载器实现"""

    async def _get_playwright_instance(self):
        """获取 playwright 实例"""
        return async_playwright()

    def _get_viewport_size_class(self):
        """获取 ViewportSize 类"""
        return ViewportSize
