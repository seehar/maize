import platform


def fix_windows_aiohttp_proxy_error():
    """
    修复 windows 系统使用 aiohttp 的代理时的错误
    """
    system = platform.system().lower()

    if system == "windows":
        import asyncio

        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
