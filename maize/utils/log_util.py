from logging import INFO
from logging import Formatter
from logging import Logger
from logging import StreamHandler


LOG_FORMAT = f"%(asctime)s [%(name)s] %(levelname)s: %(message)s"


class LoggerManager:
    logger = {}

    @classmethod
    def get_logger(
        cls, name: str = "default", log_level=None, log_format=LOG_FORMAT
    ) -> Logger:
        key = (name, log_level)

        def gen_logger():
            logger_formatter = Formatter(log_format)
            logger_handler = StreamHandler()
            logger_handler.setFormatter(logger_formatter)
            logger_handler.setLevel(log_level or INFO)

            _logger = Logger(name=name)
            _logger.addHandler(logger_handler)
            _logger.setLevel(log_level or INFO)
            cls.logger[key] = _logger
            return _logger

        return cls.logger.get(key, None) or gen_logger()


get_logger = LoggerManager.get_logger
