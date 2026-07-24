"""
统计数据上传模型。

在 :class:`~maize.common.model.statistics_model.SpiderStatistics` 基础上
附加进程和爬虫标识信息，用于将统计数据上报到监控平台。
"""

from maize.common.model.statistics_model import SpiderStatistics


class MaizeUploadModel(SpiderStatistics):
    """
    统计数据上传模型。

    继承 :class:`SpiderStatistics`，附加爬虫实例标识字段。

    :ivar pid: 进程 ID，默认 0
    :ivar stat_time: 统计时间戳字符串，默认为空
    :ivar spider_name: 爬虫名称，默认为空
    :ivar project_name: 项目名称，默认为空
    :ivar container_id: 容器 ID，默认为空
    """

    pid: int = 0
    stat_time: str = ""
    spider_name: str = ""
    project_name: str = ""
    container_id: str = ""
