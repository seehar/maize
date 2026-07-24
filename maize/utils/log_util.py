"""
日志工具，基于 ContextVar 管理 Spider 配置上下文，提供统一的 Logger 创建和缓存。
"""

import sys
from contextvars import ContextVar
from logging import INFO, Formatter, Logger, StreamHandler
from typing import TYPE_CHECKING, ClassVar, Optional

from maize.utils.project_util import load_class

if TYPE_CHECKING:
    from maize.settings import SpiderSettings

LOG_FORMAT = "%(asctime)s | %(threadName)s | %(module)s.%(funcName)s:%(lineno)d | %(levelname)s - %(message)s"

# 使用 ContextVar 存储当前的 spider_settings
_current_settings: ContextVar[Optional["SpiderSettings"]] = ContextVar("spider_settings", default=None)


def set_spider_settings(settings: "SpiderSettings") -> None:
    """
    设置当前的 spider settings 到上下文中

    :param settings: SpiderSettings 实例
    """
    _current_settings.set(settings)


def get_spider_settings() -> Optional["SpiderSettings"]:
    """
    从上下文中获取当前的 spider settings

    :return: SpiderSettings 实例或 None
    """
    return _current_settings.get()


class LoggerManager:
    """
    日志管理器，按 (name, log_level) 缓存 Logger 实例，避免重复创建。
    """

    logger: ClassVar[dict] = {}

    @classmethod
    def get_logger(
        cls,
        spider_settings: Optional["SpiderSettings"] = None,
        name: str = "default",
        log_level: int | str | None = None,
        log_format: str = LOG_FORMAT,
    ) -> Logger:
        """
        获取或创建 Logger 实例。

        :param spider_settings: Spider 配置，为 None 时从 ContextVar 获取
        :param name: Logger 名称，默认 "default"
        :param log_level: 日志级别，默认 INFO
        :param log_format: 日志格式字符串
        :return: Logger 实例
        """
        # 如果没有传入 spider_settings，则从上下文中获取
        if spider_settings is None:
            spider_settings = get_spider_settings()

        key = (name, log_level)

        def get_logger_handler():
            if spider_settings is not None:
                logger_handler_path = spider_settings.logger_handler
                if logger_handler_path:
                    logger_handler_cls = load_class(logger_handler_path)
                    return logger_handler_cls()
            logger_formatter = Formatter(log_format)
            logger_handler = StreamHandler(stream=sys.stdout)
            logger_handler.setFormatter(logger_formatter)
            logger_handler.setLevel(log_level or INFO)
            return logger_handler

        def gen_logger():
            logger_handler = get_logger_handler()
            _logger = Logger(name=name)
            _logger.addHandler(logger_handler)
            _logger.setLevel(log_level or INFO)
            cls.logger[key] = _logger
            return _logger

        return cls.logger.get(key, None) or gen_logger()


get_logger = LoggerManager.get_logger
