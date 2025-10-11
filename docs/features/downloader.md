# Downloader 下载器

## 下载器列表

`maize` 内置了一些常用的下载器：

- `maize.AioHttpDownloader`: 基于 aiohttp 封装的下载器
- `maize.HTTPXDownloader`: 基于 httpx 封装的下载器
- `maize.downloader.playwright_downloader.PlaywrightDownloader`: 基于 playwright 封装的下载器


## 自定义下载器

如果使用过程中，有特殊需求，需要自定义下载器，可以继承 `BaseDownloader` 实现自定义下载器。

```python
import typing

from maize import BaseDownloader, Request, Response

if typing.TYPE_CHECKING:
    from maize.core.crawler import Crawler


class CustomDownloader(BaseDownloader):

    def __init__(self, crawler: "Crawler"):
        super().__init__(crawler)

    async def open(self):
        await super().open()
        # 您可以在这里初始化自定义下载器

    async def close(self):
        await super().close()
        # 您可以在这里关闭自定义下载器

    async def download(self, request: Request) -> typing.Optional[Response]:
        """
        实现自定义下载逻辑
        :param request: 请求对象
        :return: 响应对象
        """
    
    @staticmethod
    def structure_response(
        request: Request, response: typing.Any, body: bytes
    ) -> Response:
        """
        构造响应对象
        :param request: 请求对象
        :param response: 自定义响应，您可以修改对象为您需要的格式
        :param body: 响应体
        :return: 响应对象
        """

    async def process_error_request(self, request: Request):
        """
        处理超过最大重试次数的请求。
        此方法不强制实现，如果您未实现，则丢弃超过最大重试次数的请求。
        :param request:
        :return:
        """
```

## 示例

您也可以参考 `maize.AioHttpDownloader` 的源码实现，您的下载器需要使用异步的方式，否则无法发挥 `maize` 的性能。

```python
import typing

from aiohttp import BaseConnector
from aiohttp import BasicAuth
from aiohttp import ClientResponse
from aiohttp import ClientSession
from aiohttp import ClientTimeout
from aiohttp import TCPConnector
from aiohttp import TraceConfig
from aiohttp import TraceRequestStartParams

from maize.downloader.base.base_downloader import BaseDownloader
from maize.common.http.request import Request
from maize.common.http import Response

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
```
