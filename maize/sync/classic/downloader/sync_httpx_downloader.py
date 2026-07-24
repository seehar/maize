"""基于 httpx 的同步下载器。

与异步版 ``HTTPXDownloader`` 对应，使用 ``httpx.Client`` 发起同步请求。
httpx 同步模式与异步模式 API 一致，零额外依赖。

连接池复用：``open()`` 时创建共享 ``httpx.Client``，``download()`` 复用该 client。
仅当 per-request proxy 与全局 proxy 不同时，创建临时 client（与 SyncLiteSpider.fetch 一致）。
"""

import typing

import httpx
from httpx import Proxy

from maize.common.http import Response
from maize.common.http.request import Request
from maize.common.model.download_response_model import DownloadResponse
from maize.sync.classic.downloader.sync_base_downloader import SyncBaseDownloader

if typing.TYPE_CHECKING:
    from maize.sync.classic.crawler.sync_crawler import SyncCrawler


class SyncHttpxDownloader(SyncBaseDownloader):
    """基于 httpx.Client 的同步下载器，复用连接池。"""

    def __init__(self, crawler: "SyncCrawler"):
        super().__init__(crawler)
        self._timeout: httpx.Timeout | None = None
        self.httpx_proxy: Proxy | None = None
        self._client: httpx.Client | None = None

    def open(self):
        super().open()
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

        # 创建共享 client，复用连接池
        self._client = httpx.Client(
            timeout=self._timeout,
            proxy=self.httpx_proxy,
        )

    def download(self, request: Request) -> typing.Union[DownloadResponse, Request]:
        if not self._client:
            raise RuntimeError("Client not initialized. Did you call open()?")

        request_proxy = self._get_proxy(request)

        try:
            # per-request proxy 或 max_redirects 与全局不同时，创建临时 client
            need_temp_client = (
                request_proxy is not None and request_proxy != self.httpx_proxy
            ) or request.max_redirects != 20
            if need_temp_client:
                client = httpx.Client(
                    timeout=self._timeout,
                    proxy=request_proxy,
                    max_redirects=request.max_redirects,
                )
                should_close = True
            else:
                client = self._client
                should_close = False

            try:
                self.logger.debug(rf"request downloading: {request.url}, method: {request.method}")
                headers = request.get_headers_sync()
                response = client.request(
                    request.method,
                    request.url,
                    headers=headers,
                    data=request.data,  # type: ignore[arg-type]
                    json=request.json,
                    params=request.params,
                    cookies=request.cookies,  # type: ignore[arg-type]
                    follow_redirects=request.follow_redirects,
                )
                body = response.content
            finally:
                if should_close:
                    client.close()
        except Exception as e:
            if new_request := self._download_retry(request, e):
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
        return Response[None, httpx.Response](
            url=request.url,
            headers=dict(response.headers),
            status=response.status_code,
            body=body,
            request=request,
            source_response=response,
        )

    def close(self):
        super().close()
        if self._client:
            self._client.close()
            self._client = None
