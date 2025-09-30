from typing import Any, Union, TYPE_CHECKING

from maize import BaseDownloader, Request, Response
from maize.common.model.download_response_model import DownloadResponse
if TYPE_CHECKING:
    from maize.core.crawler import Crawler


class CurlCffiDownloader(BaseDownloader):
    """
    基于 curl_cffi 的下载器
    """

    def __init__(self, crawler: "Crawler"):
        super().__init__(crawler)
        # 可以从 settings 中读取 curl_cffi 相关配置，例如 impersonate 类型等
        self.impersonate = getattr(crawler.settings, 'CURL_CFFI_IMPERSONATE', None)

    async def download(self, request: Request) -> Union[DownloadResponse, Request]:
        """
        使用 curl_cffi 发起请求并返回结果

        :param request: 要下载的请求对象
        :return: DownloadResponse 对象或重试后的 Request 对象
        """
        try:
            # 准备 curl_cffi 请求参数
            kwargs = {
                "url": request.url,
                "method": request.method,
                "headers": await request.get_headers(),
                "params": request.params,
                "data": request.data,
                "json": request.json,
                "cookies": request.cookies,
                "impersonate": self.impersonate,
                "proxies": {"http": request.proxy, "https": request.proxy} if request.proxy else None,
            }

            # 注意：curl_cffi 是同步阻塞的，需要在 asyncio 线程池中运行
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.request(**kwargs)
            )

            # 构造统一响应对象
            structured_response = self.structure_response(request, response, response.content)

            return DownloadResponse(
                url=structured_response.url,
                headers=dict(structured_response.headers),
                request=request,
                body=structured_response.body,
                text=structured_response.text,
                status=structured_response.status,
                cookie_list=structured_response.cookie_list,
                source_response=response,
            )

        except Exception as e:
            self.logger.error(f"Error downloading {request}: {e}")
            # 尝试重试机制
            retry_request = await self._download_retry(request, e)
            if retry_request:
                return retry_request
            # 如果不重试或达到最大重试次数，则返回原始请求（或根据需求处理）
            return request

    @staticmethod
    def structure_response(request: Request, response: Any, body: bytes) -> Response:
        """
        将 curl_cffi 的响应对象转换为统一的 Response 对象

        :param request: 原始请求对象
        :param response: curl_cffi 的响应对象
        :param body: 响应体 bytes
        :return: 统一的 Response 对象
        """
        # 提取响应头
        headers = {}
        for key, value in response.headers.items():
            headers[key] = value

        # 创建统一的 Response 对象
        return Response(
            url=str(response.url),
            headers=headers,
            request=request,
            body=body,
            status=response.status_code,
            source_response=response,
        )
