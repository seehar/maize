class ResponseVerifyException(Exception):
    """响应校验错误"""


class TransformTypeException(TypeError):
    pass


class OutputException(Exception):
    pass


class SpiderTypeException(TypeError):
    pass


class ItemInitException(Exception):
    pass


class DecodeException(Exception):
    pass


class EncodeException(Exception):
    pass


class StartRequestsNotImplementedException(NotImplementedError):
    """start_requests method not implemented"""

    pass
