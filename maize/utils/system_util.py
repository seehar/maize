import os
import platform
from typing import Optional


def fix_windows_aiohttp_proxy_error():  # pragma: no cover
    """
    修复 windows 系统使用 aiohttp 的代理时的错误
    """
    system = platform.system().lower()

    if system == "windows":
        import asyncio

        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


def get_container_id() -> Optional[str]:
    """
    获取容器id

    :return:
    """
    if not os.path.exists("/proc/self/mountinfo"):
        return None

    with open("/proc/self/mountinfo", "r", encoding="utf-8") as f:
        for line in f.readlines():
            if "/var/lib/docker/containers" not in line:
                continue
            if container_id := line.split("/var/lib/docker/containers/")[-1].split("/")[0]:
                return container_id
    return None
