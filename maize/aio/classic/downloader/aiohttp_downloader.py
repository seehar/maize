"""
基于 aiohttp 的异步下载器。

支持会话复用、代理隧道、SSL 验证配置和请求追踪。
"""

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

from maize.base.downloader.base_downloader import BaseDownloader
from maize.common.http import Response
from maize.common.http.request import Request
from maize.common.model.download_response_model import DownloadResponse

if typing.TYPE_CHECKING:
    from maize.aio.classic.crawler.crawler import Crawler


class AioHttpDownloader(BaseDownloader):
    """
    aiohttp 下载器实现。

    根据 ``use_session`` 配置决定是否复用 ClientSession，
    支持全局代理隧道和请求级代理。

    :param crawler: Crawler 实例，用于获取配置和日志
    """

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
        """
        初始化下载器资源。

        从配置中读取超时、SSL 验证、代理等参数，
        创建 TCPConnector 和 TraceConfig；若启用会话复用则创建 ClientSession。
        """
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
        """
        下载单个请求。

        根据 use_session 决定复用会话或创建临时会话，
        失败时尝试重试，重试耗尽后返回带错误原因的 DownloadResponse。

        :param request: 待下载的请求对象
        :return: 成功返回包含 Response 的 DownloadResponse，重试时返回新 Request，失败返回带 reason 的 DownloadResponse
        """
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
        """
        将 aiohttp ClientResponse 转换为框架统一 Response。

        :param request: 原始请求
        :param response: aiohttp 原始响应
        :param body: 已读取的响应体字节
        :return: 框架统一的 Response 实例
        """
        return Response[None, ClientResponse](
            url=request.url,
            headers=dict(response.headers),
            status=response.status,
            body=body,
            request=request,
            source_response=response,
        )

    async def send_request(self, session: ClientSession, request: Request) -> ClientResponse:
        """
        通过 ClientSession 发送 HTTP 请求。

        合并请求级代理与全局代理隧道，请求级代理优先。

        :param session: aiohttp ClientSession 实例
        :param request: 待发送的请求对象
        :return: aiohttp ClientResponse
        """
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
        """
        请求开始时的追踪回调，记录 debug 日志。

        :param _session: ClientSession（未使用）
        :param _trace_config_ctx: 追踪上下文（未使用）
        :param params: 包含 url 和 method 的追踪参数
        """
        self.logger.debug(rf"request downloading: {params.url}, method: {params.method}")

    async def close(self):
        """
        关闭下载器，释放 connector 和 session 资源。
        """
        await super().close()
        if self.connector:
            await self.connector.close()

        if self.session:
            await self.session.close()
