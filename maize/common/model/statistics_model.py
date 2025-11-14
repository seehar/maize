from maize import Field
from maize.common.model.base_model import BaseModel


class SpiderStatistics(BaseModel):
    # 下载总量
    download_total: int = 0

    # 下载成功量
    download_success_count: int = 0

    # 下载失败量
    download_fail_count: int = 0

    # 下载失败原因统计
    download_fail_reason: dict[str, int] = Field(default={})

    # 下载状态码统计
    download_status: dict[str, int] = Field(default={})

    # 解析成功量
    parse_success_count: int = 0

    # 解析失败量
    parse_fail_count: int = 0

    # pipeline 成功量
    pipeline_success_count: int = 0

    # pipeline 失败量
    pipeline_fail_count: int = 0
