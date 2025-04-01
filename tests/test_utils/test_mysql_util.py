import pytest

from maize.utils.mysql_util import MysqlUtil


@pytest.skip(reason="mysql test", allow_module_level=True)
@pytest.mark.asyncio
class TestMysqlUtil:
    @staticmethod
    async def get_mysql_instance() -> MysqlUtil:
        mysql_util = MysqlUtil(host="localhost", user="root", password="123456", db="maize")
        await mysql_util.open()
        return mysql_util

    async def test_insert(self):
        mysql = await self.get_mysql_instance()
        sql = "insert into baidu_spider (title, url) values ('test', 'xxx')"
        row = await mysql.execute(sql)
        assert row == 1
        await mysql.close()

    async def test_insert_many(self):
        mysql = await self.get_mysql_instance()
        sql = "insert into baidu_spider (title, url) values (%s, %s)"
        data_list = [(f"title_{i}", f"url_{i}") for i in range(10)]
        row = await mysql.executemany(sql, data_list)
        assert row == 10
        await mysql.close()
