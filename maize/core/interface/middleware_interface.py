from abc import ABC
from abc import abstractmethod


class MiddlewareInterface(ABC):
    @abstractmethod
    async def process_request(self, request):
        """
        处理请求的方法，可在请求发送前进行处理。

        :param request: 请求对象
        :type request: Request
        """
        pass

    @abstractmethod
    async def process_response(self, request, response):
        """
        处理响应的方法，可在接收到响应后进行处理。

        :param request: 请求对象
        :type request: Request
        :param response: 响应对象
        :type response: Response
        """
        pass

    @abstractmethod
    async def process_error(self, request, error):
        """
        处理错误的方法，可在发生错误时进行处理。

        :param request: 请求对象
        :type request: Request
        :param error: 错误对象
        :type error: Exception
        """
        pass
