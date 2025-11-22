import asyncio
import re
from abc import ABCMeta, abstractmethod
from collections import defaultdict
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Generic,
    Protocol,
    TypeVar,
    Union,
)

import ujson

from maize import BaseDownloader, Request, Response
from maize.common.downloader.page_pool import PagePool
from maize.common.model.download_response_model import DownloadResponse
from maize.common.model.rpa_model import InterceptRequest, InterceptResponse

if TYPE_CHECKING:
    from maize.core.crawler import Crawler

# 定义泛型类型变量
PlaywrightT = TypeVar("PlaywrightT")
BrowserT = TypeVar("BrowserT")
BrowserContextT = TypeVar("BrowserContextT")
PageT = TypeVar("PageT")
ViewportSizeT = TypeVar("ViewportSizeT")
CookieT = TypeVar("CookieT")
DownloadT = TypeVar("DownloadT")
ResponseT = TypeVar("ResponseT")


# 定义轻量协议用于路由和请求对象的类型提示，避免直接依赖第三方类型或使用 Any
class _RouteProtocol(Protocol):
    async def abort(self) -> None:  # pragma: no cover - simple protocol
        ...

    async def continue_(self) -> None:  # pragma: no cover - simple protocol
        ...


class _RequestProtocol(Protocol):
    # 不同驱动可能使用不同字段名(resource_type 或 resourceType)
    resource_type: str | None
    resourceType: str | None  # noqa: N815 - matches third-party library naming
    url: str


class BaseBrowserDownloader(
    BaseDownloader,
    Generic[
        PlaywrightT,
        BrowserT,
        BrowserContextT,
        PageT,
        ViewportSizeT,
        CookieT,
        DownloadT,
        ResponseT,
    ],
    metaclass=ABCMeta,
):
    """Playwright/Patchright 通用基类，抽取公共逻辑"""

    def __init__(self, crawler: "Crawler"):
        super().__init__(crawler)
        self.playwright: PlaywrightT | None = None
        self.browser: BrowserT | None = None
        self.context: BrowserContextT | None = None
        self.page_pool: PagePool | None = None

        self._timeout: float | None = None
        self._use_session: bool | None = None

        self._use_stealth_js: bool | None = None
        self._stealth_js_path: Path | str | None = None
        rpa_settings = self.crawler.settings.rpa
        self.__rpa_headless = rpa_settings.headless
        self.__rpa_driver_type = rpa_settings.driver_type
        self.__rpa_user_agent = rpa_settings.user_agent
        self.__rpa_timeout = self.crawler.settings.request.request_timeout
        self.__rpa_window_size = rpa_settings.window_size
        self.__rpa_executable_path = rpa_settings.executable_path
        self.__rpa_download_path = rpa_settings.download_path
        self.__rpa_render_time = rpa_settings.render_time or 0
        self.__rpa_custom_argument = rpa_settings.custom_argument
        self.__rpa_endpoint_url = rpa_settings.endpoint_url
        self.__rpa_slow_mo = rpa_settings.slow_mo
        self.__rpa_url_regexes = rpa_settings.url_regexes
        self.__rpa_url_regexes_save_all = rpa_settings.url_regexes_save_all
        self.__rpa_skip_resource_types = rpa_settings.skip_resource_types
        self.__rpa_skip_url_patterns = rpa_settings.skip_url_patterns
        self.__rpa_wait_until = rpa_settings.wait_until
        self.__proxy: str = self.crawler.settings.proxy.proxy_url
        self.__proxy_username: str = self.crawler.settings.proxy.proxy_username
        self.__proxy_password: str = self.crawler.settings.proxy.proxy_password
        self.__view_size: ViewportSizeT | None = None
        self._cache_data: dict[str, list[InterceptResponse]] = {}

        # flag to ensure we only register context routes once per downloader
        self._context_route_initialized: bool = False

        if self.__rpa_url_regexes_save_all and self.__rpa_url_regexes:
            self.logger.warning(
                "获取完拦截的数据后, 请主动调用PlaywrightDriver的clear_cache()方法清空拦截的数据，否则数据会一直累加，导致内存溢出"
            )

    @abstractmethod
    async def _get_playwright_instance(self):
        """获取 playwright 实例（子类实现，返回 async_playwright()）

        返回任意类型的 playright 上下文（类型依实现而定），子类需要实现。
        """
        raise NotImplementedError

    @abstractmethod
    def _get_viewport_size_class(self):
        """获取 ViewportSize 类（子类实现）"""
        raise NotImplementedError

    async def open(self):
        # 打开下载器，初始化播放引擎等资源
        await super().open()

        self._timeout = self.crawler.settings.request.request_timeout * 1000
        self._use_session = self.crawler.settings.request.use_session

        self._use_stealth_js = self.crawler.settings.rpa.use_stealth_js
        self._stealth_js_path = self.crawler.settings.rpa.stealth_js_path

        viewport_size_class = self._get_viewport_size_class()
        self.__view_size = viewport_size_class(width=self.__rpa_window_size[0], height=self.__rpa_window_size[1])

        # 获取并发数设置，用于页面池大小
        concurrency = self.crawler.settings.concurrency or 10
        self.page_pool = PagePool(crawler=self.crawler, max_pages=concurrency)

        if self._use_session:
            playwright_context = await self._get_playwright_instance()
            self.playwright = await playwright_context.start()
            self.browser = await self._get_browser(self.playwright)
            await self._gen_context_and_page()

    async def on_response(self, response: ResponseT) -> None:
        """响应拦截处理（异步）

        根据配置的正则匹配拦截的响应并缓存。
        """
        for regex in self.__rpa_url_regexes:
            if re.search(regex, response.request.url):
                intercept_request = InterceptRequest(
                    url=response.request.url,
                    headers=response.request.headers,
                    data=response.request.post_data_buffer,
                )

                body = await response.body()
                intercept_response = InterceptResponse(
                    request=intercept_request,
                    url=response.url,
                    headers=response.headers,
                    content=body,
                    status_code=response.status,
                )
                if self.__rpa_url_regexes_save_all and regex in self._cache_data:
                    self._cache_data[regex].append(intercept_response)
                else:
                    self._cache_data[regex] = [intercept_response]

    async def handle_download(self, download: DownloadT) -> None:
        """下载处理（异步）

        将下载的文件保存到指定路径并删除临时文件。
        """
        download_path = await download.path()
        suggested_filename = download.suggested_filename
        await download.save_as(download_path.parent / suggested_filename)

        original_file_path = Path(download_path)
        if original_file_path.exists():
            original_file_path.unlink()

    async def close(self) -> None:
        """关闭所有资源并清理（异步）"""
        # 关闭页面池
        if self.page_pool:
            await self.page_pool.close_all()
            self.page_pool = None

        if self.context:
            await self.context.close()
            self.context = None

        if self.browser:
            await self.browser.close()
            self.browser = None

        if self.playwright:
            await self.playwright.stop()
            self.playwright = None

        await super().close()

    async def download(self, request: Request) -> Union[DownloadResponse, Request]:
        """下载请求"""
        response = ""
        cookies = []
        page: PageT | None = None
        context = None

        try:
            if self._use_session:
                # 使用页面池获取页面（session 模式）
                if not self.context:
                    await self._gen_context_and_page()

                page = await self.page_pool.acquire_page(self.context)

                # 设置下载和响应拦截（每次获取页面时重新设置）
                page.on("download", self.handle_download)
                if self.__rpa_url_regexes:
                    page.on("response", self.on_response)

                if request.cookies:
                    await self.context.add_cookies(request.cookies)

                # 添加更好的错误处理和超时控制
                try:
                    self.logger.info(f"Navigating to {request.url}")
                    await page.goto(
                        request.url,
                        timeout=self._timeout,
                        wait_until=self.__rpa_wait_until,
                    )
                    self.logger.info(
                        f"Navigation completed (wait_until: {self.__rpa_wait_until}), waiting for render time: {self.__rpa_render_time}s"
                    )
                    await asyncio.sleep(self.__rpa_render_time)
                    response = await page.content()
                    cookies = await self.context.cookies()
                    self.logger.info(f"Successfully retrieved content from {request.url}")
                except Exception as e:
                    self.logger.error(f"Page navigation error for {request.url}: {e}")
                    # 检查页面状态
                    if page:
                        try:
                            page_state = "closed" if page.is_closed() else "open"
                            self.logger.info(f"Page state: {page_state}")
                        except Exception as child_e:
                            self.logger.info(f"Error checking page state: {child_e}")
                    raise e

            else:
                # 非 session 模式：为每个请求创建独立的 browser/ context
                playwright_context = await self._get_playwright_instance()
                async with playwright_context as playwright:
                    browser = await self._get_browser(playwright)

                    # 如果使用远程浏览器连接(CDP)，使用已存在的 context
                    if self.__rpa_endpoint_url:
                        context = browser.contexts[0]
                        if self.__proxy:
                            self.logger.warning(
                                "使用 RPA_ENDPOINT_URL 连接远程浏览器时，代理需要在远程浏览器启动时配置"
                            )
                    else:
                        # 否则创建新的 context
                        context_kwargs = {
                            "user_agent": self.__rpa_user_agent,
                            "screen": self.__view_size,
                            "viewport": self.__view_size,
                        }
                        proxy_config = self._get_proxy_config()
                        if proxy_config:
                            context_kwargs["proxy"] = proxy_config

                        context = await browser.new_context(**context_kwargs)
                        if self._use_stealth_js:
                            await context.add_init_script(path=self._stealth_js_path)

                    if request.cookies:
                        await context.add_cookies(request.cookies)

                    # 为非 session context 注册资源类型跳过的路由（如果配置了）
                    if self.__rpa_skip_resource_types:
                        try:
                            _res = context.route("**/*", self._route_handler)
                            # 某些实现返回 coroutine，需要 await；某些实现为同步注册，直接返回 None
                            if asyncio.iscoroutine(_res):
                                await _res
                        except Exception as e:
                            # 忽略无法注册路由的错误（不是所有驱动都支持 route）
                            self.logger.debug(f"Failed to register route handler on non-session context, error: {e}")

                    page = await context.new_page()
                    page.on("download", self.handle_download)

                    await page.goto(
                        request.url,
                        timeout=self._timeout,
                        wait_until=self.__rpa_wait_until,
                    )
                    await page.wait_for_load_state()
                    await asyncio.sleep(self.__rpa_render_time)
                    response = await page.content()
                    cookies = await context.cookies()
            return self.structure_response(request, response, cookies)

        except Exception as e:
            self.logger.error(f"Error during request: {e}")
            if new_request := await self._download_retry(request, e):
                return new_request

            download_response = DownloadResponse()
            download_response.reason = str(e)
            return download_response
        finally:
            # 清理资源
            if self._use_session and page:
                await self.page_pool.release_page(page)
            elif not self._use_session:
                # 非 session 模式：需要清理 page 和 context
                try:
                    # 关闭 page
                    if page and not page.is_closed():
                        await page.close()
                except Exception as e:
                    self.logger.debug(f"Failed to close page: {e}")

                try:
                    # 关闭 context（仅在非远程浏览器模式下）
                    # 远程浏览器的 context 不应该由我们关闭
                    if context and not self.__rpa_endpoint_url:
                        await context.close()
                except Exception as e:
                    self.logger.debug(f"Failed to close context: {e}")

    def structure_response(self, request: Request, response: str, cookies: list[CookieT]) -> DownloadResponse:
        """构建并返回 DownloadResponse 对象"""
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
        response_instance = Response(
            url=request.url,
            headers={},
            text=response,
            request=request,
            cookie_list=cookie_list,
            driver=self,
            source_response=None,  # 由于使用页面池，不再有固定的page引用
        )
        download_response = DownloadResponse()
        download_response.response = response_instance
        return download_response

    def _get_proxy_config(self) -> dict | None:
        """构建代理配置字典"""
        if not self.__proxy:
            return None

        # 确保代理地址格式正确
        proxy_server = self.__proxy
        if not proxy_server.startswith(("http://", "https://", "socks5://")):
            proxy_server = f"http://{proxy_server}"

        proxy_config = {"server": proxy_server}

        if self.__proxy_username and self.__proxy_password:
            proxy_config["username"] = self.__proxy_username
            proxy_config["password"] = self.__proxy_password

        self.logger.debug(f"代理配置: server={proxy_server}, with_auth={bool(self.__proxy_username)}")
        return proxy_config

    async def _get_browser(self, playwright: PlaywrightT) -> BrowserT:
        """获取 browser 实例"""
        if self.__rpa_endpoint_url:
            browser = await getattr(playwright, self.__rpa_driver_type).connect_over_cdp(
                endpoint_url=self.__rpa_endpoint_url,
                timeout=self._timeout,
                slow_mo=self.__rpa_slow_mo,
                headers=self.__rpa_user_agent,
            )
        else:
            browser = await getattr(playwright, self.__rpa_driver_type).launch(
                timeout=self._timeout,
                headless=self.__rpa_headless,
                args=self.__rpa_custom_argument,
                executable_path=self.__rpa_executable_path,
                downloads_path=self.__rpa_download_path,
            )
        return browser

    async def _gen_context_and_page(self):
        """生成 context 和 page"""
        if self.__rpa_endpoint_url:
            self.context = self.browser.contexts[0]
            # 使用远程浏览器连接时，记录代理配置提示
            if self.__proxy:
                self.logger.warning(
                    "使用 RPA_ENDPOINT_URL 连接远程浏览器时，代理需要在远程浏览器启动时配置，而不是在 context 级别配置"
                )
            return

        context_kwargs = {
            "user_agent": self.__rpa_user_agent,
            "screen": self.__view_size,
            "viewport": self.__view_size,
        }
        # 只在非远程连接模式下应用代理配置
        proxy_config = self._get_proxy_config()
        if proxy_config:
            context_kwargs["proxy"] = proxy_config

        self.context = await self.browser.new_context(**context_kwargs)
        if self._use_stealth_js:
            await self.context.add_init_script(path=self._stealth_js_path)

        # 为 session context 注册跳过资源类型的路由（如果配置了），只注册一次
        if self.__rpa_skip_resource_types and not self._context_route_initialized:
            try:
                # 在一些实现中 context.route 返回 coroutine，需要 await；在另一些实现中为同步方法
                _res = self.context.route("**/*", self._route_handler)
                if asyncio.iscoroutine(_res):
                    await _res
                self._context_route_initialized = True
            except Exception as e:
                # 并非所有浏览器驱动都支持 route；静默失败并打印调试信息
                self.logger.debug(f"无法在 session context 上注册路由处理器，error: {e}")

        # 不再创建单个page，页面池会在需要时创建页面

    def get_response(self, url_regex: str) -> InterceptResponse | None:
        """获取第一个匹配的拦截响应（如果有）。"""
        response_list = self._cache_data.get(url_regex)
        return response_list[0] if response_list else None

    def get_all_response(self, url_regex: str) -> list[InterceptResponse]:
        """获取所有匹配的拦截响应列表（可能为空）。"""
        return self._cache_data.get(url_regex, [])

    def get_text(self, url_regex: str) -> str | None:
        """获取第一个匹配拦截响应的文本内容，如果不存在返回 None。"""
        resp = self.get_response(url_regex)
        return resp.content.decode() if resp else None

    def get_all_text(self, url_regex: str) -> list[str]:
        """获取所有匹配拦截响应的文本内容列表。"""
        return [response.content.decode() for response in self.get_all_response(url_regex)]

    def get_json(self, url_regex: str) -> dict | None:
        """尝试将第一个匹配的拦截响应解析为 JSON 并返回，失败返回 None。"""
        text = self.get_text(url_regex)
        return ujson.loads(text) if text else None

    def get_all_json(self, url_regex: str) -> list[dict]:
        """将所有匹配的拦截响应解析为 JSON 列表并返回。"""
        return [ujson.loads(text) for text in self.get_all_text(url_regex)]

    def clear_cache(self) -> None:
        """清空内部缓存的数据（同步）。"""
        self._cache_data = defaultdict(list)

    class PageOperationContext:
        """页面操作上下文管理器，确保页面正确释放"""

        def __init__(self, downloader: "BaseBrowserDownloader"):
            self.downloader = downloader
            self.page: PageT | None = None

        async def __aenter__(self) -> PageT:
            """进入上下文并获取页面（异步）。"""
            if not self.downloader.context:
                await self.downloader._gen_context_and_page()

            self.page = await self.downloader.page_pool.acquire_page(self.downloader.context)
            return self.page

        async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
            """退出上下文并释放页面（异步）。"""
            if self.page:
                await self.downloader.page_pool.release_page(self.page)
                self.page = None

    def get_page(self) -> "PageOperationContext":
        """
        获取页面操作上下文管理器
        使用示例：
        async with downloader.get_page() as page:
            # 在此处使用page进行操作
            await page.goto("https://example.com")
        """
        return self.PageOperationContext(self)

    async def _route_handler(self, route: _RouteProtocol, request: _RequestProtocol) -> None:
        """路由处理器：根据配置的资源类型列表或 URL 模式中止特定请求（异步）。"""
        try:
            url = request.url

            # 检查 URL 模式黑名单
            if self.__rpa_skip_url_patterns and any(
                re.search(pattern, url) for pattern in self.__rpa_skip_url_patterns
            ):
                try:
                    await route.abort()
                    self.logger.debug(f"已拦截匹配 URL: {url[:100]}")
                    return
                except Exception as e:
                    self.logger.warning(f"路由中止请求失败: {e}")

            # 检查资源类型黑名单
            rtype = getattr(request, "resource_type", None) or getattr(request, "resourceType", None)
            if rtype and self.__rpa_skip_resource_types:
                rtype_str = rtype.lower()
                if any(rtype_str == t.lower() for t in self.__rpa_skip_resource_types):
                    try:
                        await route.abort()
                        return
                    except Exception as e:
                        self.logger.warning(f"路由中止请求失败: {e}")

            try:
                await route.continue_()
            except Exception as e:
                self.logger.warning(f"路由继续请求失败: {e}")
        except Exception as e:
            self.logger.debug(f"路由处理器内部错误: {e}")
