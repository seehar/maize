"""
Tests for mysql_util
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from maize.utils.mysql_util import MysqlUtil


class TestMysqlUtil:
    """Test MysqlUtil"""

    @pytest.fixture
    def mock_aiomysql(self):
        """Create mock aiomysql"""
        with patch("maize.utils.mysql_util.aiomysql") as mock:
            yield mock

    @pytest.fixture
    def mysql_util(self, mock_aiomysql):
        """Create MysqlUtil instance"""
        return MysqlUtil(
            host="localhost",
            db="test_db",
            port=3306,
            user="test_user",
            password="test_password",
            minsize=1,
            maxsize=10,
            echo=False,
            pool_recycle=3600,
        )

    def test_init(self, mysql_util):
        """Test __init__"""
        assert mysql_util.host == "localhost"
        assert mysql_util.db == "test_db"
        assert mysql_util.port == 3306
        assert mysql_util.user == "test_user"
        assert mysql_util.password == "test_password"
        assert mysql_util.minsize == 1
        assert mysql_util.maxsize == 10
        assert mysql_util.echo is False
        assert mysql_util.pool_recycle == 3600
        assert mysql_util.pool is None

    @pytest.mark.asyncio
    async def test_open_creates_pool(self, mysql_util, mock_aiomysql):
        """Test open creates connection pool"""
        mock_pool = MagicMock()
        mock_aiomysql.create_pool = AsyncMock(return_value=mock_pool)

        await mysql_util.open()

        assert mysql_util.pool is mock_pool
        mock_aiomysql.create_pool.assert_called_once_with(
            host="localhost",
            port=3306,
            user="test_user",
            password="test_password",
            db="test_db",
            minsize=1,
            maxsize=10,
            echo=False,
            pool_recycle=3600,
        )

    @pytest.mark.asyncio
    async def test_open_skips_if_pool_exists(self, mysql_util, mock_aiomysql):
        """Test open skips creation if pool exists"""
        existing_pool = MagicMock()
        mysql_util.pool = existing_pool

        await mysql_util.open()

        mock_aiomysql.create_pool.assert_not_called()
        assert mysql_util.pool is existing_pool

    @pytest.mark.asyncio
    async def test_fetchone(self, mysql_util, mock_aiomysql):
        """Test fetchone"""
        mock_pool = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone = AsyncMock(return_value={"id": 1, "name": "test"})
        mock_cursor.execute = AsyncMock()

        mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn

        mysql_util.pool = mock_pool

        result = await mysql_util.fetchone("SELECT * FROM users WHERE id = %s", (1,))

        assert result == {"id": 1, "name": "test"}
        mock_cursor.execute.assert_called_once_with("SELECT * FROM users WHERE id = %s", (1,))

    @pytest.mark.asyncio
    async def test_fetchall(self, mysql_util, mock_aiomysql):
        """Test fetchall"""
        mock_pool = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall = AsyncMock(return_value=[{"id": 1}, {"id": 2}])
        mock_cursor.execute = AsyncMock()

        mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn

        mysql_util.pool = mock_pool

        result = await mysql_util.fetchall("SELECT * FROM users")

        assert result == [{"id": 1}, {"id": 2}]

    @pytest.mark.asyncio
    async def test_execute_success(self, mysql_util, mock_aiomysql):
        """Test execute success"""
        mock_pool = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute = AsyncMock(return_value=1)
        mock_conn.commit = AsyncMock()

        mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn

        mysql_util.pool = mock_pool

        result = await mysql_util.execute("INSERT INTO users (name) VALUES (%s)", ("test",))

        assert result == 1
        mock_conn.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_rollback_on_error(self, mysql_util, mock_aiomysql):
        """Test execute rolls back on error"""
        mock_pool = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute = AsyncMock(side_effect=Exception("DB Error"))
        mock_conn.rollback = AsyncMock()

        mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn

        mysql_util.pool = mock_pool

        with pytest.raises(Exception, match="DB Error"):
            await mysql_util.execute("INSERT INTO users (name) VALUES (%s)", ("test",))

        mock_conn.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_executemany_success(self, mysql_util, mock_aiomysql):
        """Test executemany success"""
        mock_pool = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.executemany = AsyncMock(return_value=2)
        mock_conn.commit = AsyncMock()

        mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn

        mysql_util.pool = mock_pool

        result = await mysql_util.executemany(
            "INSERT INTO users (name) VALUES (%s)",
            [("test1",), ("test2",)],
        )

        assert result == 2
        mock_conn.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_executemany_rollback_on_error(self, mysql_util, mock_aiomysql):
        """Test executemany rolls back on error"""
        mock_pool = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.executemany = AsyncMock(side_effect=Exception("DB Error"))
        mock_conn.rollback = AsyncMock()

        mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn

        mysql_util.pool = mock_pool

        with pytest.raises(Exception, match="DB Error"):
            await mysql_util.executemany(
                "INSERT INTO users (name) VALUES (%s)",
                [("test1",), ("test2",)],
            )

        mock_conn.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_close(self, mysql_util, mock_aiomysql):
        """Test close"""
        mock_pool = MagicMock()
        mock_pool.close = MagicMock()
        mock_pool.wait_closed = AsyncMock()
        mysql_util.pool = mock_pool

        await mysql_util.close()

        mock_pool.close.assert_called_once()
        mock_pool.wait_closed.assert_called_once()
        assert mysql_util.pool is None

    @pytest.mark.asyncio
    async def test_close_when_pool_is_none(self, mysql_util, mock_aiomysql):
        """Test close when pool is None"""
        mysql_util.pool = None

        await mysql_util.close()

        # Should not raise
        mock_aiomysql.create_pool.assert_not_called()
