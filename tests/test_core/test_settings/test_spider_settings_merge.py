"""
Tests for SpiderSettings merge and redis_url.
"""

from maize.settings.spider_settings import SpiderSettings


class TestSpiderSettingsMerge:
    """Test SpiderSettings.merge_settings."""

    def test_merge_updates_changed_fields(self):
        base = SpiderSettings()
        other = SpiderSettings()
        other.concurrency = 10
        other.project_name = "merged"

        result = base.merge_settings(other)
        assert result is base
        assert base.concurrency == 10
        assert base.project_name == "merged"

    def test_merge_preserves_unchanged_fields(self):
        base = SpiderSettings()
        base.project_name = "original"
        other = SpiderSettings()
        other.project_name = "original"  # same, won't trigger update
        other.concurrency = 20  # only change concurrency

        base.merge_settings(other)
        assert base.concurrency == 20
        assert base.project_name == "original"

    def test_merge_with_identical_settings_no_change(self):
        base = SpiderSettings()
        other = SpiderSettings()
        original_concurrency = base.concurrency
        base.merge_settings(other)
        assert base.concurrency == original_concurrency


class TestSpiderSettingsMergeFromDict:
    """Test SpiderSettings.merge_settings_from_dict."""

    def test_merge_updates_fields_from_dict(self):
        settings = SpiderSettings()
        settings.merge_settings_from_dict({"concurrency": 5, "project_name": "test"})
        assert settings.concurrency == 5
        assert settings.project_name == "test"

    def test_merge_preserves_fields_not_in_dict(self):
        settings = SpiderSettings()
        settings.project_name = "original"
        settings.merge_settings_from_dict({"concurrency": 3})
        assert settings.concurrency == 3
        assert settings.project_name == "original"

    def test_merge_returns_self(self):
        settings = SpiderSettings()
        result = settings.merge_settings_from_dict({"concurrency": 1})
        assert result is settings

    def test_merge_nested_dict(self):
        settings = SpiderSettings()
        settings.merge_settings_from_dict({"redis": {"use_redis": True, "host": "rds.example.com"}})
        assert settings.redis.use_redis is True
        assert settings.redis.host == "rds.example.com"

    def test_merge_empty_dict_no_change(self):
        settings = SpiderSettings()
        original_concurrency = settings.concurrency
        settings.merge_settings_from_dict({})
        assert settings.concurrency == original_concurrency


class TestSpiderSettingsRedisUrl:
    """Test SpiderSettings.redis_url property."""

    def test_default_redis_url(self):
        settings = SpiderSettings()
        url = settings.redis_url
        assert url.startswith("redis://")
        assert "6379" in url

    def test_redis_url_with_password(self):
        settings = SpiderSettings()
        settings.redis.host = "localhost"
        settings.redis.port = 6379
        settings.redis.db = 0
        settings.redis.password = "secret"
        url = settings.redis_url
        assert url.startswith("redis://")
        assert "secret" in url

    def test_redis_url_with_username_and_password(self):
        settings = SpiderSettings()
        settings.redis.username = "admin"
        settings.redis.password = "pass"
        url = settings.redis_url
        assert "admin" in url
        assert "pass" in url

    def test_redis_url_custom_host_port_db(self):
        settings = SpiderSettings()
        settings.redis.host = "10.0.0.1"
        settings.redis.port = 6380
        settings.redis.db = 3
        url = settings.redis_url
        assert "10.0.0.1" in url
        assert "6380" in url
        assert url.endswith("/3")
