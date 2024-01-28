# 日志配置及使用

`maize` 的日志默认使用 `Python` 自带的 `logging` 模块。
但是您可以很方便的替换为您想用的日志模块，比如 `loguru`。示例：

```python
import logging
import sys

from loguru import logger as loguru_logger


class InterceptHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.logger = loguru_logger
        self.logger.remove()
        self.logger.add(
            sys.stdout,
            level="DEBUG",  # 请注意，此处的日志级别会覆盖配置文件中的日志级别
            format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "  # 时间
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
```

在配置文件中指定您的日志模块

```python
LOGGER_HANDLER = "the.logger.path.InterceptHandler"  # 请替换为实际路径
```
