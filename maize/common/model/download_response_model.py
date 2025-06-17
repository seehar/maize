from dataclasses import dataclass
from typing import Generic
from typing import Optional
from typing import TypeVar

from maize.common.http.response import Response


Driver = TypeVar("Driver")
R = TypeVar("R")


@dataclass
class DownloadResponse(Generic[Driver, R]):
    # 响应
    response: Optional[Response[Driver, R]] = None

    # 失败原因
    reason: Optional[str] = None
