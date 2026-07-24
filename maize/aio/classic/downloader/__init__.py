"""
Classic 异步下载器包。

提供 AioHttp、HTTPX、Playwright、Patchright 等多种下载器实现。
"""

from maize.aio.classic.downloader.aiohttp_downloader import AioHttpDownloader
from maize.aio.classic.downloader.httpx_downloader import HTTPXDownloader

try:
    from maize.aio.classic.downloader.patchright_downloader import PatchrightDownloader
except ImportError:
    PatchrightDownloader = None

try:
    from maize.aio.classic.downloader.playwright_downloader import PlaywrightDownloader
except ImportError:
    PlaywrightDownloader = None

__all__ = [
    "AioHttpDownloader",
    "HTTPXDownloader",
    "PatchrightDownloader",
    "PlaywrightDownloader",
]
