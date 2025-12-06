"""
Item 清洗中间件

清洗和标准化 Item 数据
"""

import re
from typing import TYPE_CHECKING

from maize.middlewares.base_middleware import PipelineMiddleware

if TYPE_CHECKING:
    from maize.common.items import Item
    from maize.spider.spider import Spider


class ItemCleanerMiddleware(PipelineMiddleware):
    """
    Item 数据清洗中间件

    执行操作:
    - 去除字符串的前后空白字符
    - 移除 HTML 标签
    - 标准化空白字符
    - 将空字符串转换为 None

    配置项:
        - strip_whitespace: 去除前后空白字符（默认: True）
        - remove_html: 移除 HTML 标签（默认: False）
        - normalize_whitespace: 将多个空格替换为单个空格（默认: True）
        - empty_to_none: 将空字符串转换为 None（默认: False）
        - excluded_fields: 要排除清洗的字段列表（可选）
    """

    async def open(self):
        pass

    async def close(self):
        pass

    def __init__(
        self,
        settings=None,
        strip_whitespace=True,
        remove_html=False,
        normalize_whitespace=True,
        empty_to_none=False,
        excluded_fields=None,
    ):
        """
        初始化 Item 清洗中间件

        :param settings: 爬虫配置
        :param strip_whitespace: 是否去除空白字符
        :param remove_html: 是否移除 HTML 标签
        :param normalize_whitespace: 是否标准化空白字符
        :param empty_to_none: 是否将空字符串转换为 None
        :param excluded_fields: 要排除清洗的字段
        """
        super().__init__(settings)
        self.strip_whitespace = strip_whitespace
        self.remove_html = remove_html
        self.normalize_whitespace = normalize_whitespace
        self.empty_to_none = empty_to_none
        self.excluded_fields = excluded_fields or []

        # 编译正则表达式模式
        self.html_pattern = re.compile(r"<[^>]+>")
        self.whitespace_pattern = re.compile(r"\s+")

    @classmethod
    def from_crawler(cls, crawler):
        """
        从 crawler 创建中间件实例

        :param crawler: Crawler 实例
        :return: ItemCleanerMiddleware 实例
        """
        settings = crawler.settings

        strip_whitespace = getattr(settings, "strip_whitespace", True)
        remove_html = getattr(settings, "remove_html", False)
        normalize_whitespace = getattr(settings, "normalize_whitespace", True)
        empty_to_none = getattr(settings, "empty_to_none", False)
        excluded_fields = getattr(settings, "excluded_fields", None)

        return cls(
            settings,
            strip_whitespace=strip_whitespace,
            remove_html=remove_html,
            normalize_whitespace=normalize_whitespace,
            empty_to_none=empty_to_none,
            excluded_fields=excluded_fields,
        )

    def _clean_value(self, value):
        """
        清洗单个值

        :param value: 要清洗的值
        :return: 清洗后的值
        """
        # 只处理字符串
        if not isinstance(value, str):
            return value

        # 移除 HTML 标签
        if self.remove_html:
            value = self.html_pattern.sub("", value)

        # 去除空白字符
        if self.strip_whitespace:
            value = value.strip()

        # 标准化空白字符
        if self.normalize_whitespace:
            value = self.whitespace_pattern.sub(" ", value)

        # 将空字符串转换为 None
        if self.empty_to_none and value == "":
            return None

        return value

    async def process_item_before(self, item: "Item", spider: "Spider") -> "Item | None":
        """
        在管道处理前清洗 Item 字段

        :param item: 要清洗的 Item
        :param spider: 爬虫实例
        :return: 清洗后的 Item
        """
        # 获取所有 Item 字段
        if hasattr(item.__class__, "model_fields"):
            # Pydantic v2
            fields = item.__class__.model_fields.keys()
        elif hasattr(item.__class__, "__fields__"):
            # Pydantic v1
            fields = item.__class__.__fields__.keys()
        else:
            # 回退到所有属性
            fields = [k for k in dir(item) if not k.startswith("_")]

        # 清洗每个字段
        for field in fields:
            # 跳过排除的字段
            if field in self.excluded_fields:
                continue

            # 跳过私有字段和特殊属性
            if field.startswith("_") or field.startswith("__"):
                continue

            # 获取并清洗值
            if hasattr(item, field):
                value = getattr(item, field, None)

                # 处理列表
                if isinstance(value, list):
                    cleaned_list = [self._clean_value(v) for v in value]
                    setattr(item, field, cleaned_list)
                # 处理单个值
                else:
                    cleaned_value = self._clean_value(value)
                    setattr(item, field, cleaned_value)

        return item
