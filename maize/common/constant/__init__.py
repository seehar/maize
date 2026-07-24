"""
常量定义包。

集中管理爬虫框架的枚举常量，包括模板文件、HTTP 方法、下载器、日志级别、管道和 RPA 相关配置。
"""

from .command_constant import TemplateFile
from .request_constant import Method
from .setting_constant import (
    LogLevelEnum,
    PipelineEnum,
    RPADriverTypeEnum,
    RPAResourceTypeEnum,
    RPAWaitUntilEnum,
    SpiderDownloaderEnum,
    SyncPipelineEnum,
    SyncSpiderDownloaderEnum,
)
