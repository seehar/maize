import re


class StringUtil:
    @staticmethod
    def camel_to_snake(camel_string: str) -> str:
        """
        驼峰命名法转蛇形
        :param camel_string:
        @return:
        """
        return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", camel_string).lower()
