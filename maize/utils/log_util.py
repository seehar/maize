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
    logger: ClassVar[dict] = {}

    @classmethod
    def get_logger(
        cls,
        spider_settings: Optional["SpiderSettings"] = None,
        name: str = "default",
        log_level: int | str | None = None,
        log_format: str = LOG_FORMAT,
    ) -> Logger:
        # 如果没有传入 spider_settings，则从上下文中获取
        if spider_settings is None:
            spider_settings = get_spider_settings()
            if spider_settings is None:
                raise ValueError(
                    "spider_settings is required. Please pass it explicitly or set it using set_spider_settings()"
                )

        key = (name, log_level)

        def get_logger_handler():
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
