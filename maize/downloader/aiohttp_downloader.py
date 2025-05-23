import typing

from aiohttp import BaseConnector
from aiohttp import BasicAuth
from aiohttp import ClientResponse
from aiohttp import ClientSession
from aiohttp import ClientTimeout
from aiohttp import TCPConnector
from aiohttp import TraceConfig
from aiohttp import TraceRequestStartParams

from maize.common.http import Response
from maize.common.http.request import Request
from maize.common.model.download_response_model import DownloadResponse
from maize.downloader.base_downloader import BaseDownloader


if typing.TYPE_CHECKING:
    from maize.core.crawler import Crawler


class AioHttpDownloader(BaseDownloader):
    def __init__(self, crawler: "Crawler"):
        super().__init__(crawler)
        self.session: typing.Optional[ClientSession] = None
        self.connector: typing.Optional[BaseConnector] = None

        self._verify_ssl: typing.Optional[bool] = None
        self._timeout: typing.Optional[ClientTimeout] = None
        self._use_session: typing.Optional[bool] = None
        self.trace_config: typing.Optional[TraceConfig] = None

        self.proxy_tunnel: typing.Optional[str] = None
        self.proxy_auth: typing.Optional[BasicAuth] = None

    async def open(self):
        await super().open()

        request_timeout = self.crawler.settings.REQUEST_TIMEOUT
        self._timeout = ClientTimeout(total=request_timeout)
        self._verify_ssl = self.crawler.settings.VERIFY_SSL
        self._use_session = self.crawler.settings.USE_SESSION

        self.proxy_tunnel = self.crawler.settings.PROXY_TUNNEL
        proxy_tunnel_username = self.crawler.settings.PROXY_TUNNEL_USERNAME
        proxy_tunnel_password = self.crawler.settings.PROXY_TUNNEL_PASSWORD
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

            else:
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
