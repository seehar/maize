"""
基于 Playwright 的浏览器下载器。

继承 BaseBrowserDownloader 的公共逻辑，提供标准 Playwright 驱动支持。
"""

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

from maize.aio.classic.downloader.base_browser_downloader import BaseBrowserDownloader


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
