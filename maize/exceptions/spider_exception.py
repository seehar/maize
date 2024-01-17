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


class ItemAttributeException(Exception):
    pass


class DecodeException(Exception):
    pass
