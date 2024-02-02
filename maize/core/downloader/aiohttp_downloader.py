import typing

from aiohttp import BaseConnector
from aiohttp import BasicAuth
from aiohttp import ClientResponse
from aiohttp import ClientSession
from aiohttp import ClientTimeout
from aiohttp import TCPConnector
from aiohttp import TraceConfig
from aiohttp import TraceRequestStartParams

from maize.core.downloader.base_downloader import BaseDownloader
from maize.core.http.request import Request
from maize.core.http.response import Response


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

        request_timeout = self.crawler.settings.getint("REQUEST_TIMEOUT")
        self._timeout = ClientTimeout(total=request_timeout)
        self._verify_ssl = self.crawler.settings.getbool("VERIFY_SSL")
        self._use_session = self.crawler.settings.getbool("USE_SESSION")

        self.proxy_tunnel = self.crawler.settings.get("PROXY_TUNNEL")
        proxy_tunnel_username = self.crawler.settings.get("PROXY_TUNNEL_USERNAME")
        proxy_tunnel_password = self.crawler.settings.get("PROXY_TUNNEL_PASSWORD")
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

    async def download(self, request: Request) -> typing.Optional[Response | Request]:
        try:
            if self._use_session:
                response = await self.send_request(self.session, request)
                body = await response.content.read()

            else:
                connector = TCPConnector(verify_ssl=self._verify_ssl)
                async with ClientSession(
                    connector=connector,
                    timeout=self._timeout,
                    trace_configs=[self.trace_config],
                ) as session:
                    response = await self.send_request(session, request)
                    body = await response.content.read()

        except Exception as e:
            if new_request := await self._download_retry(request, e):
                return new_request

            self.logger.error(f"Error during request: {e}")
            return None

        return self.structure_response(request, response, body)

    @staticmethod
    def structure_response(
        request: Request, response: ClientResponse, body: bytes
    ) -> Response:
        return Response(
            url=request.url,
            headers=dict(response.headers),
            status=response.status,
            body=body,
            request=request,
        )

    async def send_request(
        self, session: ClientSession, request: Request
    ) -> ClientResponse:
        if request.proxy_username and request.proxy_password:
            proxy_auth = BasicAuth(request.proxy_username, request.proxy_password)
        else:
            proxy_auth = self.proxy_auth

        return await session.request(
            method=request.method,
            url=request.url,
            params=request.params,
            data=request.data,
            headers=request.headers,
            cookies=request.cookies,
            proxy=request.proxy or self.proxy_tunnel,
            proxy_auth=proxy_auth,
        )

    async def request_start(
        self, _session, _trace_config_ctx, params: TraceRequestStartParams
    ):
        self.logger.debug(
            rf"request downloading: {params.url}, method: {params.method}"
        )

    async def close(self):
        await super().close()
        if self.connector:
            await self.connector.close()

        if self.session:
            await self.session.close()
