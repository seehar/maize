"""
重试相关异常。
"""


class MaxRetryException(Exception):
    """最大重试次数异常"""


class RetryNotCatchException(Exception):
    """重试时不需要捕获的异常"""
