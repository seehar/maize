"""基于 requests 的同步下载器。

requests 是同步爬虫生态中最成熟的 HTTP 库，提供丰富的特性（session、auth、streaming 等）。
本下载器需安装 ``requests``（非 maize 默认依赖）。
"""

import typing

from maize.common.http import Response
from maize.common.http.request import Request
from maize.common.model.download_response_model import DownloadResponse
from maize.sync.classic.downloader.sync_base_downloader import SyncBaseDownloader

if typing.TYPE_CHECKING:
    from maize.sync.classic.crawler.sync_crawler import SyncCrawler

try:
    import requests
except ImportError:
    requests = None  # type: ignore[assignment]


class SyncRequestsDownloader(SyncBaseDownloader):
    """基于 requests.Session 的同步下载器。

    需要额外安装 ``requests``：``pip install requests``。
    """

    def __init__(self, crawler: "SyncCrawler"):
        super().__init__(crawler)
        self._session: requests.Session | None = None
        self._timeout: float | None = None
        self._proxies: dict[str, str] | None = None

    def open(self):
        super().open()
        if requests is None:
            raise ImportError("requests is not installed. Install it with: pip install requests")

        self._session = requests.Session()
        self._timeout = self.crawler.settings.request.request_timeout

        proxy_tunnel = self.crawler.settings.proxy.proxy_url
        if proxy_tunnel:
            proxy_url = f"http://{proxy_tunnel}"
            self._proxies = {"http": proxy_url, "https": proxy_url}

    def download(self, request: Request) -> typing.Union[DownloadResponse, Request]:
        try:
            headers = request.get_headers_sync()
            proxy_url = self._get_request_proxy(request)

            response = self._session.request(  # type: ignore[union-attr]
                method=request.method,
                url=request.url,
                headers=headers,
                data=request.data,
                json=request.json,
                params=request.params,
                cookies=request.cookies,
                proxies={"http": proxy_url, "https": proxy_url} if proxy_url else None,
                allow_redirects=request.follow_redirects,
                timeout=self._timeout,
            )
            body = response.content
        except Exception as e:
            if new_request := self._download_retry(request, e):
                return new_request

            self.logger.error(f"Error during request: {e}")
            return DownloadResponse(reason=str(e))

        structure_response = self.structure_response(request, response, body)
        return DownloadResponse(response=structure_response)

    def _get_request_proxy(self, request: Request) -> str | None:
        if request.proxy:
            if request.proxy_username and request.proxy_password:
                return f"http://{request.proxy_username}:{request.proxy_password}@{request.proxy}"
            return f"http://{request.proxy}"
        return None

    @staticmethod
    def structure_response(
        request: Request, response: "requests.Response", body: bytes
    ) -> Response[None, "requests.Response"]:
        return Response[None, requests.Response](
            url=request.url,
            headers=dict(response.headers),
            status=response.status_code,
            body=body,
            request=request,
            source_response=response,
        )

    def close(self):
        super().close()
        if self._session:
            self._session.close()
            self._session = None
