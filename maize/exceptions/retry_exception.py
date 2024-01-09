class MaxRetryException(Exception):
    """最大重试次数异常"""

    pass


class RetryNotCatchException(Exception):
    """重试时不需要捕获的异常"""

    pass
