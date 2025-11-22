import asyncio
from typing import TYPE_CHECKING

from maize.utils.log_util import get_logger

if TYPE_CHECKING:
    from playwright.async_api import BrowserContext, Page

    from maize.core.crawler import Crawler


class PagePool:
    """页面连接池，用于管理多个并发页面"""

    def __init__(self, crawler: "Crawler", max_pages: int = 10):
        self.max_pages = max_pages
        self.available_pages: list[Page] = []
        self.in_use_pages: set[Page] = set()
        self._lock = asyncio.Lock()
        self.logger = get_logger(crawler.settings, self.__class__.__name__, crawler.settings.log_level)

    async def acquire_page(self, context: "BrowserContext") -> "Page":
        """获取一个页面"""
        async with self._lock:
            if self.available_pages:
                # 复用可用页面
                page = self.available_pages.pop()
                try:
                    # 检查页面是否仍然有效
                    if page.is_closed():
                        page = await context.new_page()
                except Exception as e:
                    self.logger.warning(f"Failed to check page availability: {e}")
                    # 如果页面有问题，创建新页面
                    page = await context.new_page()
            elif len(self.in_use_pages) + len(self.available_pages) < self.max_pages:
                # 创建新页面
                page = await context.new_page()
            else:
                # 等待有页面可用
                while not self.available_pages:
                    await asyncio.sleep(0.1)
                page = self.available_pages.pop()

            self.in_use_pages.add(page)
            return page

    async def release_page(self, page: "Page"):
        """释放页面回连接池"""
        async with self._lock:
            if page in self.in_use_pages:
                self.in_use_pages.remove(page)
                # 移除事件监听器，避免重复绑定
                try:
                    page.remove_listener("download", None)
                    page.remove_listener("response", None)
                except Exception as e:
                    self.logger.debug(f"Failed to remove event listeners: {e}")
                self.available_pages.append(page)

    async def close_all(self):
        """关闭所有页面"""
        async with self._lock:
            for page in self.available_pages + list(self.in_use_pages):
                try:
                    await page.close()
                except Exception as e:
                    self.logger.warning(f"Failed to close page: {e}")
            self.available_pages.clear()
            self.in_use_pages.clear()
