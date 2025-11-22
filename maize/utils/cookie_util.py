from typing import Any


class CookieUtil:
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
        字符串类型的 cookie 转 list
        :param cookie_string:
        :param domain:
        :param path:
        :param expires:
        :param http_only:
        :param secure:
        :param same_site:
        @return:
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
