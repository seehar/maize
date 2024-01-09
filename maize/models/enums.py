from enum import IntEnum
from enum import unique


@unique
class SpiderStatus(IntEnum):
    """爬虫状态"""

    DEFAULT = 0  # 默认装填
    INITIALIZED = 1  # 爬虫已初始化
    RUNNING = 2  # 爬虫正在运行
    PAUSED = 3  # 爬虫已暂停
    STOPPED = 4  # 爬虫已停止
    COMPLETED = 5  # 爬虫已完成
    ERROR = 6  # 爬虫发生错误
    IDLE = 7  # 爬虫处于空闲状态
    TERMINATING = 8  # 爬虫正在终止
    RESUMING = 9  # 爬虫正在恢复
    HALTED = 10  # 爬虫已暂停运行
    RESTARTING = 11  # 爬虫正在重新启动
