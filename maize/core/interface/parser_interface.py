from abc import ABC
from abc import abstractmethod


class ParserInterface(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def parse(self, content):
        """
        解析给定的内容，并返回解析结果。

        Parameters:
        - content (str): 待解析的内容。

        Returns:
        - dict: 解析结果，通常是一个字典。
        """
        pass

    @abstractmethod
    def extract_links(self, content):
        """
        从给定的内容中提取链接，并返回链接列表。

        Parameters:
        - content (str): 待提取链接的内容。

        Returns:
        - list: 包含提取到的链接的列表。
        """
        pass

    # 可选的扩展方法，根据需要实现
    def preprocess(self, content):
        """
        在正式解析之前，可以对内容进行预处理。

        Parameters:
        - content (str): 待预处理的内容。

        Returns:
        - str: 预处理后的内容。
        """
        return content

    def postprocess(self, parsed_data):
        """
        在解析完成后，可以对解析结果进行后处理。

        Parameters:
        - parsed_data (dict): 解析得到的结果。

        Returns:
        - dict: 后处理后的结果。
        """
        return parsed_data
