"""
字符串工具，提供命名格式转换。
"""

import re


class StringUtil:
    """
    字符串工具类，提供命名格式转换的静态方法。
    """

    @staticmethod
    def camel_to_snake(camel_string: str) -> str:
        """
        驼峰命名法转蛇形
        :param camel_string:
        @return:
        """
        return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", camel_string).lower()
