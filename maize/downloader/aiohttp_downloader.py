import typing

from aiohttp import (
    BaseConnector,
    BasicAuth,
    ClientResponse,
    ClientSession,
    ClientTimeout,
    TCPConnector,
    TraceConfig,
    TraceRequestStartParams,
)

from maize.common.http import Response
from maize.common.http.request import Request
from maize.common.model.download_response_model import DownloadResponse
from maize.downloader.base.base_downloader import BaseDownloader

if typing.TYPE_CHECKING:
    from maize.core.crawler import Crawler


class AioHttpDownloader(BaseDownloader):
    def __init__(self, crawler: "Crawler"):
        super().__init__(crawler)
        self.session: ClientSession | None = None
        self.connector: BaseConnector | None = None

        self._verify_ssl: bool | None = None
        self._timeout: ClientTimeout | None = None
        self._use_session: bool | None = None
        self.trace_config: TraceConfig | None = None

        self.proxy_tunnel: str | None = None
        self.proxy_auth: BasicAuth | None = None

    async def open(self):
        await super().open()

        request_timeout = self.crawler.settings.request.request_timeout
        self._timeout = ClientTimeout(total=request_timeout)
        self._verify_ssl = self.crawler.settings.request.verify_ssl
        self._use_session = self.crawler.settings.request.use_session

        self.proxy_tunnel = self.crawler.settings.proxy.proxy_url
        proxy_tunnel_username = self.crawler.settings.proxy.proxy_username
        proxy_tunnel_password = self.crawler.settings.proxy.proxy_password
        if proxy_tunnel_username and proxy_tunnel_password:
            self.proxy_auth = BasicAuth(proxy_tunnel_username, proxy_tunnel_password)

        self.connector = TCPConnector(verify_ssl=self._verify_ssl)
        self.trace_config = TraceConfig()
        self.trace_config.on_request_start.append(self.request_start)
        if self._use_session:
            self.session = ClientSession(
                connector=self.connector,
                timeout=self._timeout,
                trace_configs=[self.trace_config],
            )

    async def download(self, request: Request) -> typing.Union[DownloadResponse, Request]:
        await self.random_wait()
        try:
            if self._use_session:
                response = await self.send_request(self.session, request)
                body = await response.content.read()
                structure_response = self.structure_response(request, response, body)
                return DownloadResponse(response=structure_response)

            connector = TCPConnector(verify_ssl=self._verify_ssl)
            async with ClientSession(
                connector=connector,
                timeout=self._timeout,
                trace_configs=[self.trace_config],
            ) as session:
                response = await self.send_request(session, request)
                body = await response.content.read()
            structure_response = self.structure_response(request, response, body)
            return DownloadResponse(response=structure_response)

        except Exception as e:
            if new_request := await self._download_retry(request, e):
                return new_request

            self.logger.error(f"Error during request: {e}")
            return DownloadResponse(reason=str(e))

    @staticmethod
    def structure_response(request: Request, response: ClientResponse, body: bytes) -> Response[None, ClientResponse]:
        return Response[None, ClientResponse](
            url=request.url,
            headers=dict(response.headers),
            status=response.status,
            body=body,
            request=request,
            source_response=response,
        )

    async def send_request(self, session: ClientSession, request: Request) -> ClientResponse:
        if request.proxy_username and request.proxy_password:
            proxy_auth = BasicAuth(request.proxy_username, request.proxy_password)
        else:
            proxy_auth = self.proxy_auth

        headers = await request.get_headers()
        return await session.request(
            method=request.method,
            url=request.url,
            params=request.params,
            data=request.data,
            json=request.json,
            headers=headers,
            cookies=request.cookies,
            proxy=request.proxy or self.proxy_tunnel,
            proxy_auth=proxy_auth,
            allow_redirects=request.follow_redirects,
            max_redirects=request.max_redirects,
        )

    async def request_start(self, _session, _trace_config_ctx, params: TraceRequestStartParams):
        self.logger.debug(rf"request downloading: {params.url}, method: {params.method}")

    async def close(self):
        await super().close()
        if self.connector:
            await self.connector.close()

        if self.session:
            await self.session.close()
