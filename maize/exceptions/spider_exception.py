"""
Spider 相关异常，包含响应校验、类型转换、输出格式等异常。
"""


class ResponseVerifyException(Exception):
    """响应校验错误"""


class TransformTypeException(TypeError):
    """
    回调返回值类型转换异常。
    """

    pass


class OutputException(Exception):
    """
    Spider 输出格式异常。
    """

    pass


class SpiderTypeException(TypeError):
    """
    Spider 类型异常。
    """

    pass


class ItemInitException(Exception):
    """
    Item 初始化异常。
    """

    pass


class DecodeException(Exception):
    """
    解码异常。
    """

    pass


class EncodeException(Exception):
    """
    编码异常。
    """

    pass


class StartRequestsNotImplementedException(NotImplementedError):
    """start_requests method not implemented"""

    pass
