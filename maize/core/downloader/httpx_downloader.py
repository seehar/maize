import typing

import httpx

from maize import BaseDownloader
from maize.core.http.request import Request
from maize.core.http.response import Response


if typing.TYPE_CHECKING:
    from maize.core.crawler import Crawler


class HTTPXDownloader(BaseDownloader):
    def __init__(self, crawler: "Crawler"):
        super().__init__(crawler)

        self._timeout: typing.Optional[httpx.Timeout] = None

    def open(self):
        super().open()
        request_timeout = self.crawler.settings.getint("REQUEST_TIMEOUT")
        self._timeout = httpx.Timeout(timeout=request_timeout)

    async def fetch(self, request: Request) -> typing.Optional[Response]:
        async with self._active(request):
            return await self.download(request)

    async def download(self, request: Request) -> typing.Optional[Response]:
        try:
            proxies = request.proxies
            async with httpx.AsyncClient(
                timeout=self._timeout, proxies=proxies
            ) as client:
                self.logger.debug(
                    rf"request downloading: {request.url}, method: {request.method}"
                )
                response = await client.request(
                    request.method,
                    request.url,
                    headers=request.headers,
                    data=request.data,
                    params=request.params,
                )
                body = await response.aread()
        except Exception as e:
            if new_request := await self._download_retry(request, e):
                return new_request

            self.logger.error(f"Error during request: {e}")
            return None
        return self.structure_response(request, response, body)

    @staticmethod
    def structure_response(
        request: Request, response: httpx.Response, body: bytes
    ) -> Response:
        return Response(
            url=request.url,
            headers=dict(response.headers),
            status=response.status_code,
            body=body,
            request=request,
        )
