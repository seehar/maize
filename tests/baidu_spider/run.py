import asyncio
import logging
import sys

# from tests.baidu_spider.spiders.baidu2 import BaiduSpider2
from loguru import logger as loguru_logger

from maize import CrawlerProcess
from maize.utils import get_settings
from tests.baidu_spider.spiders.baidu import BaiduSpider


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
        logger_opt = self.logger.opt(depth=7, exception=record.exc_info)
        logger_opt.log(record.levelno, record.getMessage())


from maize.utils.log_util import get_logger


logger = get_logger()
# get_logger().addHandler(InterceptHandler())
logging.getLogger().setLevel(10)
logging.getLogger().addHandler(InterceptHandler())


async def run():
    settings = get_settings()
    process = CrawlerProcess(settings=settings)
    await process.crawl(BaiduSpider)
    # await process.crawl(BaiduSpider2)
    await process.start()


if __name__ == "__main__":
    asyncio.run(run())
