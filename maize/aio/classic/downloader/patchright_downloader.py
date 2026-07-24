"""
基于 Patchright 的浏览器下载器。

Patchright 是 Playwright 的反检测分支，继承 BaseBrowserDownloader 的公共逻辑。
"""

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

from maize.aio.classic.downloader.base_browser_downloader import BaseBrowserDownloader


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
