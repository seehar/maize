# -*- encoding: utf-8 -*-
import sys

from loguru import logger as loguru_logger


class HandleLogger:
    def __init__(self):
        self.logger = loguru_logger
        # 清空所有设置
        self.logger.remove()
        # 添加控制台输出的格式,sys.stdout为输出到屏幕;关于这些配置还需要自定义请移步官网查看相关参数说明
        self.logger.add(
            sys.stdout,
            level="DEBUG",
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "  # 颜色>时间
            "{process.name} | "  # 进程名
            "{thread.name} | "  # 进程名
            "<cyan>{module}</cyan>.<cyan>{function}</cyan>"  # 模块名.方法名
            ":<cyan>{line}</cyan> | "  # 行号
            "<level>{level}</level>: "  # 等级
            "<level>{message}</level>",  # 日志内容
        )
        # 输出到文件的格式,注释下面的add',则关闭日志写入
        # self.logger.add(
        #     settings.LOGGER_FILENAME,
        #     level=settings.LOGGER_LEVEL,
        #     format="{time:YYYY-MM-DD HH:mm:ss} - "  # 时间
        #     "{process.name} | "  # 进程名
        #     "{thread.name} | "  # 进程名
        #     "{module}.{function}:{line} - {level} -{message}",  # 模块名.方法名:行号
        #     rotation="10 MB",
        #     encoding="utf-8",
        #     retention="1 week",  # 设置历史保留时长
        #     backtrace=True,  # 回溯
        #     diagnose=True,  # 诊断
        #     enqueue=True,  # 异步写入
        # )
        # self.logger.add(
        #     settings.LOGGER_ERROR_FILENAME,
        #     level="ERROR",
        #     format="{time:YYYY-MM-DD HH:mm:ss} - "  # 时间
        #     "{process.name} | "  # 进程名
        #     "{thread.name} | "  # 进程名
        #     "{module}.{function}:{line} - {level} -{message}",  # 模块名.方法名:行号
        #     rotation="10 MB",
        #     encoding="utf-8",
        #     retention="10 week",  # 设置历史保留时长
        #     backtrace=True,  # 回溯
        #     diagnose=True,  # 诊断
        #     enqueue=True,  # 异步写入
        #     filter=lambda record: "ERROR" in record["level"].name,
        # )

    def get_logger(self):
        return self.logger


logger = HandleLogger().get_logger()
