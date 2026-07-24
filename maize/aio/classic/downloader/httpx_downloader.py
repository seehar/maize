"""
基于 httpx 的异步下载器。

每次请求创建独立的 AsyncClient，支持请求级代理和全局代理隧道。
"""

import typing

import httpx
from httpx import Proxy

from maize.base.downloader.base_downloader import BaseDownloader
from maize.common.http import Response
from maize.common.http.request import Request
from maize.common.model.download_response_model import DownloadResponse

if typing.TYPE_CHECKING:
    from maize.aio.classic.crawler.crawler import Crawler


class HTTPXDownloader(BaseDownloader):
    """
    httpx 下载器实现。

    每次 download 创建临时 AsyncClient（httpx 0.28 不支持 per-request proxy），
    通过 Proxy 对象统一管理代理配置。

    :param crawler: Crawler 实例，用于获取配置和日志
    """

    def __init__(self, crawler: "Crawler"):
        super().__init__(crawler)

        self._timeout: httpx.Timeout | None = None
        self.httpx_proxy: Proxy | None = None

    async def open(self):
        """
        初始化下载器配置。

        从 settings 读取请求超时和代理隧道信息，构建 httpx.Proxy 和 Timeout 对象。
        """
        await super().open()
        request_timeout = self.crawler.settings.request.request_timeout

        proxy_tunnel = self.crawler.settings.proxy.proxy_url
        proxy_tunnel_username = self.crawler.settings.proxy.proxy_username
        proxy_tunnel_password = self.crawler.settings.proxy.proxy_password
        if proxy_tunnel and proxy_tunnel_username and proxy_tunnel_password:
            proxy_url = f"http://{proxy_tunnel_username}:{proxy_tunnel_password}@{proxy_tunnel}/"
            self.httpx_proxy = Proxy(url=proxy_url)
        elif proxy_tunnel:
            proxy_url = f"http://{proxy_tunnel}/"
            self.httpx_proxy = Proxy(url=proxy_url)

        self._timeout = httpx.Timeout(timeout=request_timeout)

    async def download(self, request: Request) -> typing.Union[DownloadResponse, Request]:
        """
        下载单个请求。

        创建临时 AsyncClient 发送请求，失败时尝试重试，
        重试耗尽后返回带错误原因的 DownloadResponse。

        :param request: 待下载的请求对象
        :return: 成功返回包含 Response 的 DownloadResponse，重试时返回新 Request，失败返回带 reason 的 DownloadResponse
        """
        await self.random_wait()
        try:
            proxies = self._get_proxy(request)
            async with httpx.AsyncClient(
                timeout=self._timeout,
                proxy=proxies,
                max_redirects=request.max_redirects,
            ) as client:
                self.logger.debug(rf"request downloading: {request.url}, method: {request.method}")
                headers = await request.get_headers()
                response = await client.request(
                    request.method,
                    request.url,
                    headers=headers,
                    data=request.data,
                    json=request.json,
                    params=request.params,
                    cookies=request.cookies,
                    follow_redirects=request.follow_redirects,
                )
                body = await response.aread()
        except Exception as e:
            if new_request := await self._download_retry(request, e):
                return new_request

            self.logger.error(f"Error during request: {e}")
            return DownloadResponse(reason=str(e))
        structure_response = self.structure_response(request, response, body)
        return DownloadResponse(response=structure_response)

    def _get_proxy(self, request: Request) -> Proxy | None:
        if not request.proxy:
            return self.httpx_proxy

        if request.proxy_username and request.proxy_password:
            proxy_url = f"http://{request.proxy_username}:{request.proxy_password}@{request.proxy}"
        else:
            proxy_url = f"http://{request.proxy}"
        return Proxy(url=proxy_url)

    @staticmethod
    def structure_response(request: Request, response: httpx.Response, body: bytes) -> Response[None, httpx.Response]:
        """
        将 httpx Response 转换为框架统一 Response。

        :param request: 原始请求
        :param response: httpx 原始响应
        :param body: 已读取的响应体字节
        :return: 框架统一的 Response 实例
        """
        return Response[None, httpx.Response](
            url=request.url,
            headers=dict(response.headers),
            status=response.status_code,
            body=body,
            request=request,
            source_response=response,
        )
