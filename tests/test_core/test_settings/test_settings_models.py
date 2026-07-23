"""
Tests for ProxySettings, RedisSettings, RPASettings, MiddlewareSettings.
"""

from maize.settings.spider_settings import (
    MySQLSettings,
    PipelineSettings,
    ProxySettings,
    RedisSettings,
    RPASettings,
)


class TestProxySettings:
    """Test ProxySettings."""

    def test_defaults(self):
        settings = ProxySettings()
        assert settings.proxy_url == ""
        assert settings.enabled is False
        assert settings.proxy_dict is None

    def test_proxy_dict_disabled(self):
        settings = ProxySettings(proxy_url="proxy:8080", enabled=False)
        assert settings.proxy_dict is None

    def test_proxy_dict_no_auth(self):
        settings = ProxySettings(proxy_url="proxy:8080", enabled=True)
        result = settings.proxy_dict
        assert result is not None
        assert "http" in result
        assert "proxy:8080" in result["http"]

    def test_proxy_dict_with_auth(self):
        settings = ProxySettings(proxy_url="proxy:8080", enabled=True, proxy_username="user", proxy_password="pass")
        result = settings.proxy_dict
        assert result is not None
        assert "user:pass@proxy:8080" in result["http"]

    def test_proxy_dict_empty_url(self):
        settings = ProxySettings(enabled=True, proxy_url="")
        assert settings.proxy_dict is None


class TestRedisSettings:
    """Test RedisSettings."""

    def test_defaults(self):
        settings = RedisSettings()
        assert settings.use_redis is False
        assert settings.host == "localhost"
        assert settings.port == 6379
        assert settings.db == 0
        assert settings.key_prefix == "maize"

    def test_url_no_auth(self):
        settings = RedisSettings(host="10.0.0.1", port=6380, db=3)
        url = settings.url
        assert url == "redis://10.0.0.1:6380/3"

    def test_url_with_password(self):
        settings = RedisSettings(password="secret")
        url = settings.url
        assert "secret" in url

    def test_url_with_username_and_password(self):
        settings = RedisSettings(username="admin", password="pass")
        url = settings.url
        assert "admin:pass@" in url

    def test_url_with_only_username(self):
        settings = RedisSettings(username="admin")
        url = settings.url
        assert "admin" in url


class TestRPASettings:
    """Test RPASettings."""

    def test_defaults(self):
        settings = RPASettings()
        assert settings.headless is True
        assert settings.driver_type == "chromium"
        assert settings.window_size == (1024, 800)
        assert settings.use_stealth_js is True
        assert settings.url_regexes == []
        assert settings.skip_resource_types == []

    def test_custom_values(self):
        settings = RPASettings(
            headless=False,
            driver_type="firefox",
            window_size=(1920, 1080),
            render_time=5,
        )
        assert settings.headless is False
        assert settings.driver_type == "firefox"
        assert settings.window_size == (1920, 1080)
        assert settings.render_time == 5


class TestMySQLSettings:
    """Test MySQLSettings."""

    def test_defaults(self):
        settings = MySQLSettings()
        assert settings.host == "localhost"
        assert settings.port == 3306
        assert settings.db == ""
        assert settings.user == ""
        assert settings.password == ""

    def test_custom_values(self):
        settings = MySQLSettings(host="db.example.com", port=3307, db="mydb", user="admin", password="secret")
        assert settings.host == "db.example.com"
        assert settings.port == 3307
        assert settings.db == "mydb"
        assert settings.user == "admin"
        assert settings.password == "secret"


class TestPipelineSettings:
    """Test PipelineSettings."""

    def test_defaults(self):
        settings = PipelineSettings()
        assert settings.pipelines == ["maize.EmptyPipeline"]
        assert settings.max_cache_count == 5000
        assert settings.handle_batch_max_size == 1000
        assert settings.error_max_retry_count == 5
