from dataclasses import dataclass
from typing import Optional

from maize.common.http.response import Response


@dataclass
class DownloadResponse:
    # 响应
    response: Optional[Response] = None

    # 失败原因
    reason: Optional[str] = None
