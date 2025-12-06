"""
Item 验证中间件

在 Item 进入管道前验证它们
"""

from typing import TYPE_CHECKING

from maize.middlewares.base_middleware import PipelineMiddleware

if TYPE_CHECKING:
    from maize.common.items import Item
    from maize.spider.spider import Spider


class ItemValidationMiddleware(PipelineMiddleware):
    """
    Item 验证中间件

    可以验证:
    - 必填字段是否存在
    - 字段类型是否正确
    - 字段值是否满足条件

    配置项:
        - required_fields: 必填字段名称列表（可选）
        - drop_invalid_items: 是否丢弃无效的 Item（默认: True）
        - validation_log_level: 验证错误的日志级别（默认: 'warning'）
    """

    async def open(self):
        pass

    def __init__(self, settings=None, required_fields=None, drop_invalid_items=True, log_level="warning"):
        """
        初始化 Item 验证中间件

        :param settings: 爬虫配置
        :param required_fields: 必填字段名称列表
        :param drop_invalid_items: 是否丢弃无效的 Item
        :param log_level: 验证错误的日志级别
        """
        super().__init__(settings)
        self.required_fields = required_fields or []
        self.drop_invalid_items = drop_invalid_items
        self.log_level = log_level

        # 统计信息
        self.stats = {
            "items_validated": 0,
            "items_invalid": 0,
            "items_dropped": 0,
        }

    @classmethod
    def from_crawler(cls, crawler):
        """
        从 crawler 创建中间件实例

        :param crawler: Crawler 实例
        :return: ItemValidationMiddleware 实例
        """
        settings = crawler.settings

        required_fields = getattr(settings, "required_fields", None)
        drop_invalid_items = getattr(settings, "drop_invalid_items", True)
        log_level = getattr(settings, "validation_log_level", "warning")

        return cls(
            settings, required_fields=required_fields, drop_invalid_items=drop_invalid_items, log_level=log_level
        )

    def _validate_item(self, item: "Item") -> tuple[bool, list[str]]:
        """
        验证 Item

        :param item: 要验证的 Item
        :return: (是否有效, 错误消息列表) 的元组
        """
        errors = []

        # 检查必填字段
        for field in self.required_fields:
            # 检查字段是否存在并有值
            if not hasattr(item, field):
                errors.append(f"Missing required field: {field}")
            else:
                value = getattr(item, field, None)
                if value is None or value == "":
                    errors.append(f"Required field '{field}' is empty")

        is_valid = len(errors) == 0
        return is_valid, errors

    def _log_validation_error(self, item: "Item", errors: list[str]):
        """
        记录验证错误

        :param item: Item 实例
        :param errors: 错误消息列表
        """
        message = f"Item validation failed: {', '.join(errors)}"

        if self.log_level == "debug":
            self.logger.debug(message)
        elif self.log_level == "info":
            self.logger.info(message)
        elif self.log_level == "warning":
            self.logger.warning(message)
        elif self.log_level == "error":
            self.logger.error(message)

    async def process_item_before(self, item: "Item", spider: "Spider") -> "Item | None":
        """
        在 Item 进入管道前验证

        :param item: 要验证的 Item
        :param spider: 爬虫实例
        :return: 如果有效返回 Item，如果无效且应该丢弃则返回 None
        """
        self.stats["items_validated"] += 1

        # 验证 Item
        is_valid, errors = self._validate_item(item)

        if not is_valid:
            self.stats["items_invalid"] += 1
            self._log_validation_error(item, errors)

            if self.drop_invalid_items:
                self.stats["items_dropped"] += 1
                return None

        return item

    async def close(self):
        """
        关闭时记录统计信息
        """
        self.logger.info("Item Validation Statistics:")
        for stat, count in sorted(self.stats.items()):
            self.logger.info(f"  {stat}: {count}")
