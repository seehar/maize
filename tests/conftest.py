import logging
import sys
from pathlib import Path

from loguru import logger as loguru_logger


sys.path.append(str(Path(__file__).parent.parent))


class InterceptHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.logger = loguru_logger
        self.logger.remove()
        self.logger.add(
            sys.stdout,
            level="DEBUG",
            format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "  # 颜色>时间
            "{process.name} | "  # 进程名
            "{thread.name} | "  # 进程名
            "<cyan>{module}</cyan>.<cyan>{function}</cyan>"  # 模块名.方法名
            ":<cyan>{line}</cyan> | "  # 行号
            "<level>{level}</level>: "  # 等级
            "<level>{message}</level>",  # 日志内容
        )

    def emit(self, record: logging.LogRecord):
        logger_opt = self.logger.opt(depth=6, exception=record.exc_info)
        logger_opt.log(record.levelname, record.getMessage())


logging.getLogger().setLevel(10)
logging.getLogger().addHandler(InterceptHandler())
