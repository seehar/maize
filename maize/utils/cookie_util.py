"""
Cookie 工具，提供字符串 Cookie 到结构化列表的转换。
"""

from typing import Any


class CookieUtil:
    """
    Cookie 工具类，提供 Cookie 格式转换的静态方法。
    """

    @staticmethod
    def str_cookies_to_list(
        cookie_string: str,
        domain: str,
        path: str = "",
        expires: int = -1,
        http_only: bool = False,
        secure: bool = False,
        same_site: str = "Lax",
    ) -> list[dict[str, Any]]:
        """
        将字符串类型的 Cookie 转换为结构化列表。

        :param cookie_string: Cookie 字符串，如 "name1=value1; name2=value2"
        :param domain: Cookie 所属域名
        :param path: Cookie 路径，默认 ""
        :param expires: 过期时间戳，-1 表示会话级，默认 -1
        :param http_only: 是否 HttpOnly，默认 False
        :param secure: 是否仅 HTTPS，默认 False
        :param same_site: SameSite 策略，默认 "Lax"
        :return: Cookie 字典列表
        """
        if not cookie_string:
            return []

        cookies = []
        for part in cookie_string.split("; "):
            items = part.split("=")
            if len(items) < 2:
                continue

            name = items[0]
            value = "=".join(items[1:])
            cookies.append(
                {
                    "name": name,
                    "value": value,
                    "domain": domain,
                    "path": path,
                    "expires": expires,
                    "httpOnly": http_only,
                    "secure": secure,
                    "sameSite": same_site,
                }
            )
        return cookies
