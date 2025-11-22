from typing import TYPE_CHECKING

from maize.pipelines.base_pipeline import BasePipeline
from maize.utils.log_util import get_logger
from maize.utils.mysql_util import MysqlSingletonUtil

if TYPE_CHECKING:
    from maize import Item
    from maize.settings import SpiderSettings


class MysqlPipeline(BasePipeline):
    def __init__(self, settings: "SpiderSettings"):
        super().__init__(settings=settings)
        self.mysql: MysqlSingletonUtil | None = None
        self.logger = get_logger(settings, self.__class__.__name__)

    async def open(self):
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
        await self.mysql.close()

    async def process_item(self, items: list["Item"]) -> bool:
        """
        批量处理 item
        :param items:
        @return: 成功 True，否则 False
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
        first_item = items[0]
        item_key = first_item.model_dump().keys()
        item_data_list = []
        for item in items:
            item_data_list.append([item[key] for key in item_key])

        item_key_str = ",".join(item_key)
        placeholder = ",".join(["%s"] * len(item_key))
        sql = f"insert into {first_item.__table_name__} ({item_key_str}) values ({placeholder})"
        row = await self.mysql.executemany(sql, item_data_list)
        self.logger.info(f"process item row: {row}")

    async def process_error_item(self, items: list["Item"]):
        pass
