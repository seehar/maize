import typing

from maize.core.pipelines.base_pipeline import BasePipeline
from maize.utils import MysqlUtil


if typing.TYPE_CHECKING:
    from maize import Item
    from maize.core.settings.settings_manager import SettingsManager


class MysqlPipeline(BasePipeline):
    def __init__(self, settings: "SettingsManager"):
        super().__init__(settings=settings)
        self.mysql: typing.Optional[MysqlUtil] = None

    async def open(self):
        host = self.settings.get("MYSQL_HOST")
        port = self.settings.getint("MYSQL_PORT") or 3306
        db = self.settings.get("MYSQL_DB")
        user = self.settings.get("MYSQL_USER")
        password = self.settings.get("MYSQL_PASSWORD")

        if not host or not db or not user or not password:
            raise ValueError("Mysql settings not found")

        self.mysql = MysqlUtil(
            host=host, port=port, db=db, user=user, password=password
        )
        await self.mysql.open()

    async def close(self):
        await self.mysql.close()

    async def process_item(self, items: list["Item"]):
        if not items:
            return

        first_item = items[0]
        item_key = first_item.to_dict().keys()
        item_data_list = []
        for item in items:
            item_data_list.append([item[key] for key in item_key])

        item_key_str = ",".join(item_key)
        placeholder = ",".join(["%s"] * len(item_key))
        sql = f"insert into {first_item.__table_name__} ({item_key_str}) values ({placeholder})"
        await self.mysql.executemany(sql, item_data_list)
