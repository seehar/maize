from logging import INFO
from logging import Formatter
from logging import Logger
from logging import StreamHandler
from typing import TYPE_CHECKING
from typing import Union

from maize.utils.project_util import load_class


if TYPE_CHECKING:
    from maize.settings import SettingsManager


LOG_FORMAT = f"%(asctime)s [%(name)s] %(levelname)s: %(message)s"


class LoggerManager:
    logger = {}

    @classmethod
    def get_logger(
        cls,
        settings_manager: "SettingsManager",
        name: str = "default",
        log_level: Union[int, str] = None,
        log_format: str = LOG_FORMAT,
    ) -> Logger:
        key = (name, log_level)

        def get_logger_handler():
            logger_handler_path = settings_manager.get("LOGGER_HANDLER")
            if logger_handler_path:
                logger_handler_cls = load_class(logger_handler_path)
                return logger_handler_cls()
            else:
                logger_formatter = Formatter(log_format)
                logger_handler = StreamHandler()
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
