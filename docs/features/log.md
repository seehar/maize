# 日志配置

## 简介

maize 默认使用 Python 内置的 `logging` 模块，但设计上支持灵活替换为其他日志库（如 loguru）。良好的日志记录对于调试、监控和问题排查至关重要。

### 日志级别

maize 支持以下日志级别（按严重程度递增）：

| 级别         | 说明   | 使用场景          |
|:-----------|:-----|:--------------|
| `DEBUG`    | 调试信息 | 开发调试          |
| `INFO`     | 一般信息 | 常规运行信息        |
| `WARNING`  | 警告信息 | 潜在问题          |
| `ERROR`    | 错误信息 | 错误但程序可继续运行    |
| `CRITICAL` | 严重错误 | 严重错误，程序可能无法继续 |

## 默认日志配置

### 在配置中设置日志级别

```python
from maize import SpiderSettings


settings = SpiderSettings(
    project_name="我的爬虫",
    log_level="INFO"  # 设置日志级别
)
```

或在 settings.py 中：

```python
# settings.py
from maize import SpiderSettings


class Settings(SpiderSettings):
    log_level = "DEBUG"  # 开发时使用 DEBUG
```

### 在爬虫中使用日志

```python
from maize import Spider, Response


class MySpider(Spider):
    async def parse(self, response: Response):
        # 使用不同级别的日志
        self.logger.debug("调试信息：开始解析页面")
        self.logger.info(f"正在处理: {response.url}")
        self.logger.warning("警告：响应时间较长")
        self.logger.error("错误：解析失败")
        self.logger.critical("严重错误：系统异常")
```

## 自定义日志处理器

### 使用 Loguru（推荐）

Loguru 是一个功能强大、使用简单的 Python 日志库。

**1. 安装 loguru**

```bash
pip install loguru
```

**2. 创建自定义日志处理器**

创建 `logger_util.py` 文件：

```python
# logger_util.py
import logging
import sys

from loguru import logger as loguru_logger


class InterceptHandler(logging.Handler):
    """拦截 logging 日志并转发到 loguru"""

    def __init__(self):
        super().__init__()
        self.logger = loguru_logger

        # 移除默认处理器
        self.logger.remove()

        # 添加控制台输出
        self.logger.add(
            sys.stdout,
            level="DEBUG",
            format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                   "<level>{level: <8}</level> | "
                   "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                   "<level>{message}</level>",
            colorize=True,
        )

        # 添加文件输出
        self.logger.add(
            "logs/spider_{time:YYYY-MM-DD}.log",
            rotation="00:00",  # 每天午夜轮转
            retention="30 days",  # 保留30天
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
            encoding="utf-8",
        )

    def emit(self, record: logging.LogRecord):
        """将 logging 记录转发到 loguru"""
        # 获取对应的 loguru 级别
        try:
            level = self.logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # 获取调用者信息
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        # 记录日志
        self.logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )
```

**3. 在配置中使用**

```python
# settings.py
from maize import SpiderSettings


class Settings(SpiderSettings):
    logger_handler = "your_project.logger_util.InterceptHandler"
```

或使用 SpiderSettings 对象：

```python
settings = SpiderSettings(
    logger_handler="your_project.logger_util.InterceptHandler"
)
```

### 自定义日志格式

#### 格式1：简洁格式

```python
self.logger.add(
    sys.stdout,
    format="{time:HH:mm:ss} | {level} | {message}",
    level="INFO",
)
```

输出示例：
```
14:30:45 | INFO | 正在处理: http://example.com
```

#### 格式2：详细格式

```python
self.logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
           "<level>{level: <8}</level> | "
           "<cyan>{process.name}</cyan>:<cyan>{thread.name}</cyan> | "
           "<cyan>{name}</cyan>.<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
           "<level>{message}</level>",
    colorize=True,
)
```

输出示例：
```
2024-01-15 14:30:45.123 | INFO     | MainProcess:MainThread | MySpider.parse:45 | 正在处理: http://example.com
```

#### 格式3：JSON 格式

```python
import json


def json_formatter(record):
    """JSON 格式化器"""
    log_data = {
        "time": record["time"].strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
        "level": record["level"].name,
        "logger": record["name"],
        "function": record["function"],
        "line": record["line"],
        "message": record["message"],
    }
    return json.dumps(log_data, ensure_ascii=False) + "\n"


self.logger.add(
    "logs/spider.jsonl",
    format=json_formatter,
    level="INFO",
)
```

输出示例：
```json
{"time": "2024-01-15 14:30:45.123", "level": "INFO", "logger": "MySpider", "function": "parse", "line": 45, "message": "正在处理: http://example.com"}
```

## 完整配置示例

### 示例1：开发环境配置

```python
# logger_util.py
import logging
import sys
from loguru import logger as loguru_logger


class DevelopmentHandler(logging.Handler):
    """开发环境日志配置"""

    def __init__(self):
        super().__init__()
        self.logger = loguru_logger
        self.logger.remove()

        # 控制台输出 - 彩色、详细
        self.logger.add(
            sys.stdout,
            level="DEBUG",
            format="<green>{time:HH:mm:ss.SSS}</green> | "
                   "<level>{level: <8}</level> | "
                   "<cyan>{name}</cyan>.<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
                   "<level>{message}</level>",
            colorize=True,
        )

    def emit(self, record: logging.LogRecord):
        logger_opt = self.logger.opt(depth=6, exception=record.exc_info)
        logger_opt.log(record.levelname, record.getMessage())
```

### 示例2：生产环境配置

```python
# logger_util.py
import logging
import sys
from loguru import logger as loguru_logger


class ProductionHandler(logging.Handler):
    """生产环境日志配置"""

    def __init__(self):
        super().__init__()
        self.logger = loguru_logger
        self.logger.remove()

        # 控制台输出 - 简洁、INFO 及以上
        self.logger.add(
            sys.stdout,
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
            colorize=False,
        )

        # 文件输出 - 详细、按日期轮转
        self.logger.add(
            "logs/spider_{time:YYYY-MM-DD}.log",
            rotation="00:00",
            retention="30 days",
            compression="zip",  # 压缩旧日志
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
            encoding="utf-8",
        )

        # 错误日志单独记录
        self.logger.add(
            "logs/error_{time:YYYY-MM-DD}.log",
            rotation="00:00",
            retention="90 days",
            level="ERROR",
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}\n{exception}",
            encoding="utf-8",
        )

    def emit(self, record: logging.LogRecord):
        logger_opt = self.logger.opt(depth=6, exception=record.exc_info)
        logger_opt.log(record.levelname, record.getMessage())
```

### 示例3：多环境配置

```python
# logger_util.py
import logging
import sys
import os
from loguru import logger as loguru_logger


class SmartHandler(logging.Handler):
    """根据环境变量自动选择配置"""

    def __init__(self):
        super().__init__()
        self.logger = loguru_logger
        self.logger.remove()

        # 获取环境变量
        env = os.getenv("ENVIRONMENT", "development")

        if env == "production":
            self._setup_production()
        else:
            self._setup_development()

    def _setup_development(self):
        """开发环境配置"""
        self.logger.add(
            sys.stdout,
            level="DEBUG",
            format="<green>{time:HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>",
            colorize=True,
        )

    def _setup_production(self):
        """生产环境配置"""
        self.logger.add(
            sys.stdout,
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
        )

        self.logger.add(
            "logs/spider_{time:YYYY-MM-DD}.log",
            rotation="00:00",
            retention="30 days",
            level="INFO",
            encoding="utf-8",
        )

    def emit(self, record: logging.LogRecord):
        logger_opt = self.logger.opt(depth=6, exception=record.exc_info)
        logger_opt.log(record.levelname, record.getMessage())


# 使用示例：
# export ENVIRONMENT=production  # Linux/Mac
# $env:ENVIRONMENT="production"  # Windows PowerShell
```

## 高级用法

### 1. 日志轮转

按大小轮转：
```python
self.logger.add(
    "logs/spider.log",
    rotation="10 MB",  # 每10MB创建新文件
    retention=10,      # 保留最近10个文件
)
```

按时间轮转：
```python
self.logger.add(
    "logs/spider.log",
    rotation="1 day",   # 每天创建新文件
    retention="1 week", # 保留1周
)
```

### 2. 日志压缩

```python
self.logger.add(
    "logs/spider_{time}.log",
    rotation="00:00",
    compression="zip",  # 或 "gz", "bz2", "xz"
)
```

### 3. 异步日志

```python
self.logger.add(
    "logs/spider.log",
    enqueue=True,  # 异步写入
    level="INFO",
)
```

### 4. 过滤日志

```python
def info_filter(record):
    """只记录 INFO 级别的日志"""
    return record["level"].name == "INFO"


self.logger.add(
    "logs/info.log",
    filter=info_filter,
)
```

### 5. 结构化日志

```python
# 使用 bind 添加上下文
logger = self.logger.bind(spider="MySpider", task_id=123)
logger.info("开始处理任务")

# 使用 extra 添加自定义字段
self.logger.info("处理完成", extra={"url": "http://example.com", "items": 10})
```

## 最佳实践

### 1. 开发和生产环境分离

```python
# 开发环境：详细日志、彩色输出
if os.getenv("ENV") == "dev":
    log_level = "DEBUG"
    colorize = True
else:
    # 生产环境：简洁日志、文件输出
    log_level = "INFO"
    colorize = False
```

### 2. 合理使用日志级别

```python
class MySpider(Spider):
    async def parse(self, response: Response):
        # DEBUG: 调试信息
        self.logger.debug(f"响应头: {response.headers}")

        # INFO: 正常流程
        self.logger.info(f"正在处理: {response.url}")

        # WARNING: 潜在问题
        if response.status != 200:
            self.logger.warning(f"异常状态码: {response.status}")

        # ERROR: 错误但可继续
        try:
            data = response.json()
        except Exception as e:
            self.logger.error(f"JSON 解析失败: {e}")

        # CRITICAL: 严重错误
        if critical_error:
            self.logger.critical("数据库连接失败，程序无法继续")
```

### 3. 记录有用的信息

```python
# ❌ 不好：信息不足
self.logger.info("处理完成")

# ✅ 好：包含关键信息
self.logger.info(f"处理完成 - URL: {response.url}, 耗时: {elapsed}s, 提取: {item_count}条")
```

### 4. 异常日志

```python
try:
    result = do_something()
except Exception as e:
    # 记录完整的异常堆栈
    self.logger.exception(f"操作失败: {e}")
    # 或
    self.logger.error(f"操作失败: {e}", exc_info=True)
```

### 5. 性能考虑

```python
# ❌ 不好：每次都格式化
self.logger.debug(f"数据: {large_data}")  # 即使不输出 DEBUG 日志也会格式化

# ✅ 好：使用延迟格式化
if self.logger.isEnabledFor(logging.DEBUG):
    self.logger.debug(f"数据: {large_data}")
```

## 日志分析

### 使用 grep 查看日志

```bash
# 查看错误日志
grep "ERROR" logs/spider_2024-01-15.log

# 查看特定 URL 的日志
grep "example.com" logs/spider_2024-01-15.log

# 统计错误数量
grep -c "ERROR" logs/spider_2024-01-15.log
```

### 使用 Python 分析日志

```python
import re
from collections import Counter


def analyze_log(log_file):
    """分析日志文件"""
    levels = Counter()
    errors = []

    with open(log_file, 'r', encoding='utf-8') as f:
        for line in f:
            # 提取日志级别
            match = re.search(r'\| (\w+)\s+\|', line)
            if match:
                level = match.group(1)
                levels[level] += 1

                # 收集错误信息
                if level in ('ERROR', 'CRITICAL'):
                    errors.append(line.strip())

    print(f"日志统计: {dict(levels)}")
    print(f"\n错误日志 ({len(errors)} 条):")
    for error in errors[:10]:  # 显示前10条
        print(error)


analyze_log("logs/spider_2024-01-15.log")
```

## 常见问题

### 1. 日志不显示颜色？

确保终端支持颜色，并设置 `colorize=True`。

### 2. 日志文件中文乱码？

设置正确的编码：
```python
self.logger.add("logs/spider.log", encoding="utf-8")
```

### 3. 日志文件太大？

使用日志轮转和压缩：
```python
self.logger.add(
    "logs/spider.log",
    rotation="10 MB",
    compression="zip",
    retention=10
)
```

### 4. 如何只记录爬虫日志？

使用日志名称过滤：
```python
def spider_filter(record):
    return record["name"].startswith("MySpider")

self.logger.add("logs/spider.log", filter=spider_filter)
```

## 注意事项

1. **日志级别**：生产环境使用 INFO 或 WARNING，开发环境使用 DEBUG
2. **敏感信息**：不要在日志中记录密码、密钥等敏感信息
3. **日志轮转**：设置合理的轮转策略，避免磁盘占满
4. **性能影响**：过多的日志会影响性能，合理控制日志量
5. **时区问题**：注意日志时间的时区设置

## 下一步

- [配置说明](settings.md) - 日志配置选项
- [Spider 进阶](spider.md) - 在爬虫中使用日志
