import asyncio
import platform
from pathlib import Path


def fix_windows_aiohttp_proxy_error():  # pragma: no cover
    """
    修复 windows 系统使用 aiohttp 的代理时的错误
    """
    system = platform.system().lower()

    if system == "windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


def get_container_id() -> str | None:
    """
    获取容器id

    :return:
    """
    if not Path.exists(Path("/proc/self/mountinfo")):
        return None

    with open("/proc/self/mountinfo", encoding="utf-8") as f:
        for line in f.readlines():
            if "/resolv.conf" not in line:
                continue
            if container_id := line.split("/resolv.conf")[0].split("/")[-1]:
                print(container_id)
                return container_id
    return None
