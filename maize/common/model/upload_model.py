from dataclasses import dataclass

from maize.common.model.statistics_model import SpiderStatistics


@dataclass
class MaizeUploadModel(SpiderStatistics):
    pid: int = 0
    stat_time: str = ""
    spider_name: str = ""
    project_name: str = ""
    container_id: str = ""
