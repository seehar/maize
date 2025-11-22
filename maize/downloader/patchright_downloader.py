from patchright.async_api import (
    Browser,
    BrowserContext,
    Cookie,
    Download,
    Page,
    Playwright,
    Response as PatchrightResponse,
    ViewportSize,
    async_playwright,
)

from maize.downloader.base.base_browser_downloader import BaseBrowserDownloader


class PatchrightDownloader(
    BaseBrowserDownloader[
        Playwright,
        Browser,
        BrowserContext,
        Page,
        ViewportSize,
        Cookie,
        Download,
        PatchrightResponse,
    ]
):
    """Patchright 下载器实现"""

    async def _get_playwright_instance(self):
        """获取 playwright 实例"""
        return async_playwright()

    def _get_viewport_size_class(self):
        """获取 ViewportSize 类"""
        return ViewportSize
