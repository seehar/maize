"""
maize 异常定义，包含重试、响应校验、类型转换等异常。
"""

from .retry_exception import MaxRetryException, RetryNotCatchException
from .spider_exception import ResponseVerifyException
