from playwright.async_api import (
    Browser,
    BrowserContext,
    Cookie,
    Download,
    Page,
    Playwright,
    Response as PlaywrightResponse,
    ViewportSize,
    async_playwright,
)

from maize.downloader.base.base_browser_downloader import BaseBrowserDownloader


class PlaywrightDownloader(
    BaseBrowserDownloader[
        Playwright,
        Browser,
        BrowserContext,
        Page,
        ViewportSize,
        Cookie,
        Download,
        PlaywrightResponse,
    ]
):
    """Playwright 下载器实现"""

    async def _get_playwright_instance(self):
        """获取 playwright 实例"""
        return async_playwright()

    def _get_viewport_size_class(self):
        """获取 ViewportSize 类"""
        return ViewportSize
