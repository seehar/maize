"""
MySQL 数据管道。

将 Item 批量写入 MySQL 数据库，基于 Item 的 __table_name__ 和字段自动生成 INSERT 语句。
"""

from typing import TYPE_CHECKING

from maize.pipelines.base_pipeline import BasePipeline
from maize.utils.log_util import get_logger
from maize.utils.mysql_util import MysqlSingletonUtil

if TYPE_CHECKING:
    from maize import Item
    from maize.settings import SpiderSettings


class MysqlPipeline(BasePipeline):
    """
    MySQL 数据管道，将 Item 批量插入 MySQL 表。

    通过 SpiderSettings 中的 mysql 配置建立连接，使用 executemany 批量写入。

    :param settings: 爬虫配置对象，需包含有效的 mysql 连接信息
    """

    def __init__(self, settings: "SpiderSettings"):
        super().__init__(settings=settings)
        self.mysql: MysqlSingletonUtil | None = None
        self.logger = get_logger(settings, self.__class__.__name__)

    async def open(self):
        """
        初始化 MySQL 连接。

        从 settings.mysql 读取连接参数并创建 MysqlSingletonUtil 实例。

        :raises ValueError: 当 host/db/user/password 任一配置缺失时抛出
        """
        host = self.settings.mysql.host
        port = self.settings.mysql.port or 3306
        db = self.settings.mysql.db
        user = self.settings.mysql.user
        password = self.settings.mysql.password

        if not host or not db or not user or not password:
            raise ValueError("Mysql settings not found")

        self.mysql = MysqlSingletonUtil(host=host, port=port, db=db, user=user, password=password)
        await self.mysql.open()

    async def close(self):
        """
        关闭 MySQL 连接。
        """
        await self.mysql.close()

    async def process_item(self, items: list["Item"]) -> bool:
        """
        批量处理 Item，写入 MySQL。

        :param items: 待写入的 Item 列表
        :return: 写入成功返回 True，发生异常返回 False
        """
        if not items:
            return True

        try:
            await self._process_items(items)
            return True
        except Exception as e:
            self.logger.error(f"Error processing item: {e}. items: {items}")
            return False

    async def _process_items(self, items: list["Item"]):
        """
        执行批量 INSERT 操作。

        根据第一个 Item 的字段名和 __table_name__ 生成 SQL，使用 executemany 批量插入。

        :param items: 同类型 Item 列表（字段结构一致）
        """
        first_item = items[0]
        item_key = first_item.model_dump().keys()
        item_data_list = []
        for item in items:
            item_data_list.append([getattr(item, key) for key in item_key])

        item_key_str = ",".join(item_key)
        placeholder = ",".join(["%s"] * len(item_key))
        sql = f"insert into {first_item.__table_name__} ({item_key_str}) values ({placeholder})"
        row = await self.mysql.executemany(sql, item_data_list)
        self.logger.info(f"process item row: {row}")

    async def process_error_item(self, items: list["Item"]):
        """
        处理错误 Item，当前为空实现（不额外处理失败数据）。

        :param items: 超过重试次数的 Item 列表
        """
        pass
