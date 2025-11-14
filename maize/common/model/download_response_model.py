from typing import Generic
from typing import Optional
from typing import TypeVar

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from maize.common.http.response import Response


Driver = TypeVar("Driver")
R = TypeVar("R")


class DownloadResponse(BaseModel, Generic[Driver, R]):
    """下载响应模型"""

    # 响应
    response: Optional[Response[Driver, R]] = Field(default=None, description="下载响应对象")

    # 失败原因
    reason: Optional[str] = Field(default=None, description="下载失败原因")

    model_config = ConfigDict(arbitrary_types_allowed=True)  # 允许任意类型（Response 是自定义类型）
