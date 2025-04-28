from dataclasses import dataclass
from typing import Optional

from maize.common.model.statistics_model import SpiderStatistics


@dataclass
class MaizeUploadModel:
    pid: int = 0
    now: str = ""
    spider_name: str = ""
    project_name: str = ""
    stat: Optional[SpiderStatistics] = None
