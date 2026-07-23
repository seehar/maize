"""
Tests for MysqlPipeline.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from maize.common.items import Item
from maize.pipelines.mysql_pipeline import MysqlPipeline
from maize.settings import SpiderSettings


class DemoItem(Item):
    __table_name__: str = "demo"
    name: str = ""
    age: int = 0


def _make_settings(host="localhost", db="testdb", user="root", password="pass"):
    settings = SpiderSettings()
    settings.mysql.host = host
    settings.mysql.db = db
    settings.mysql.user = user
    settings.mysql.password = password
    settings.mysql.port = 3306
    return settings


class TestMysqlPipelineOpen:
    """Test MysqlPipeline.open."""

    @pytest.mark.asyncio
    @patch("maize.pipelines.mysql_pipeline.MysqlSingletonUtil")
    async def test_open_creates_mysql_util(self, mock_util_cls):
        mock_util = MagicMock()
        mock_util.open = AsyncMock()
        mock_util_cls.return_value = mock_util

        settings = _make_settings()
        pipeline = MysqlPipeline(settings)
        await pipeline.open()

        mock_util_cls.assert_called_once()
        mock_util.open.assert_called_once()
        assert pipeline.mysql is mock_util

    @pytest.mark.asyncio
    async def test_open_raises_on_missing_config(self):
        """open() raises ValueError when host/db/user/password missing."""
        settings = SpiderSettings()
        settings.mysql.host = ""
        pipeline = MysqlPipeline(settings)
        with pytest.raises(ValueError, match="Mysql settings not found"):
            await pipeline.open()

    @pytest.mark.asyncio
    async def test_open_uses_default_port(self):
        """When port is 0 (falsy), default 3306 is used."""
        settings = _make_settings()
        settings.mysql.port = 0

        with patch("maize.pipelines.mysql_pipeline.MysqlSingletonUtil") as mock_cls:
            mock_util = MagicMock()
            mock_util.open = AsyncMock()
            mock_cls.return_value = mock_util
            pipeline = MysqlPipeline(settings)
            await pipeline.open()

            call_kwargs = mock_cls.call_args
            assert call_kwargs.kwargs["port"] == 3306


class TestMysqlPipelineClose:
    """Test MysqlPipeline.close."""

    @pytest.mark.asyncio
    async def test_close_closes_mysql(self):
        pipeline = MysqlPipeline(_make_settings())
        mock_mysql = MagicMock()
        mock_mysql.close = AsyncMock()
        pipeline.mysql = mock_mysql

        await pipeline.close()
        mock_mysql.close.assert_called_once()


class TestMysqlPipelineProcessItem:
    """Test MysqlPipeline.process_item."""

    @pytest.mark.asyncio
    async def test_empty_items_returns_true(self):
        pipeline = MysqlPipeline(_make_settings())
        assert await pipeline.process_item([]) is True

    @pytest.mark.asyncio
    async def test_successful_process_returns_true(self):
        pipeline = MysqlPipeline(_make_settings())
        pipeline._process_items = AsyncMock()
        result = await pipeline.process_item([DemoItem(name="a", age=1)])
        assert result is True
        pipeline._process_items.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_item_handles_exception(self):
        pipeline = MysqlPipeline(_make_settings())
        pipeline._process_items = AsyncMock(side_effect=RuntimeError("db error"))
        result = await pipeline.process_item([DemoItem(name="a", age=1)])
        assert result is False

    @pytest.mark.asyncio
    async def test_builds_and_executes_insert_sql(self):
        pipeline = MysqlPipeline(_make_settings())
        mock_mysql = MagicMock()
        mock_mysql.executemany = AsyncMock(return_value=2)
        pipeline.mysql = mock_mysql

        items = [
            DemoItem(name="alice", age=30),
            DemoItem(name="bob", age=25),
        ]
        await pipeline._process_items(items)

        call_args = mock_mysql.executemany.call_args
        sql = call_args.args[0]
        data = call_args.args[1]

        assert "insert into demo" in sql
        assert "name" in sql
        assert "age" in sql
        assert len(data) == 2
        assert data[0] == ["alice", 30]
        assert data[1] == ["bob", 25]

    @pytest.mark.asyncio
    async def test_single_item(self):
        pipeline = MysqlPipeline(_make_settings())
        mock_mysql = MagicMock()
        mock_mysql.executemany = AsyncMock(return_value=1)
        pipeline.mysql = mock_mysql

        await pipeline._process_items([DemoItem(name="x", age=1)])

        call_args = mock_mysql.executemany.call_args
        assert len(call_args.args[1]) == 1
