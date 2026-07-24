"""
爬虫统计模型。

记录爬虫运行期间的下载、解析、管道各阶段的成功/失败计数。
"""

from maize.common.items.field import Field
from maize.common.model.base_model import BaseModel


class SpiderStatistics(BaseModel):
    """
    爬虫运行统计数据。

    涵盖下载、解析、管道三个阶段的计数及失败原因分布。

    :ivar download_total: 下载请求总量，默认 0
    :ivar download_success_count: 下载成功量，默认 0
    :ivar download_fail_count: 下载失败量，默认 0
    :ivar download_fail_reason: 下载失败原因统计，键为原因描述，值为次数
    :ivar download_status: 下载状态码统计，键为状态码字符串，值为次数
    :ivar parse_success_count: 解析成功量，默认 0
    :ivar parse_fail_count: 解析失败量，默认 0
    :ivar pipeline_success_count: 管道处理成功量，默认 0
    :ivar pipeline_fail_count: 管道处理失败量，默认 0
    """

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
