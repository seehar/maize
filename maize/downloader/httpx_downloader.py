import typing

import httpx
from httpx import Proxy

from maize import BaseDownloader
from maize.common.http import Response
from maize.common.http.request import Request
from maize.common.model.download_response_model import DownloadResponse

if typing.TYPE_CHECKING:
    from maize.core.crawler import Crawler


class HTTPXDownloader(BaseDownloader):
    def __init__(self, crawler: "Crawler"):
        super().__init__(crawler)

        self._timeout: httpx.Timeout | None = None
        self.httpx_proxy: Proxy | None = None

    async def open(self):
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
        return Response[None, httpx.Response](
            url=request.url,
            headers=dict(response.headers),
            status=response.status_code,
            body=body,
            request=request,
            source_response=response,
        )
