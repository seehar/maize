import logging

from maize.settings import SettingsManager
from maize.settings.base_settings import BaseSettings


class TestSettingsManager:
    def test_set_settings_model(self):
        settings_manager = SettingsManager()
        settings_manager.set_settings(BaseSettings)
        concurrency = settings_manager.getint("CONCURRENCY")
        logging.info(concurrency)
        assert concurrency == BaseSettings.CONCURRENCY

    def test_set_settings_model_path(self):
        settings_manager = SettingsManager()
        settings_manager.set_settings("maize.BaseSettings")
        concurrency = settings_manager.getint("CONCURRENCY")
        logging.info(concurrency)
        assert concurrency == BaseSettings.CONCURRENCY

    @property
    def get_instance(self):
        settings_manager = SettingsManager()
        settings_manager.set_settings(BaseSettings)
        return settings_manager

    def test_get(self):
        settings_manager = self.get_instance
        downloader = settings_manager.get("DOWNLOADER")
        assert downloader == BaseSettings.DOWNLOADER

    def test_getint(self):
        settings_manager = self.get_instance
        concurrency = settings_manager.getint("CONCURRENCY")
        assert concurrency == BaseSettings.CONCURRENCY

    def test_getbool(self):
        settings_manager = self.get_instance
        concurrency = settings_manager.getbool("VERIFY_SSL")
        assert concurrency == BaseSettings.VERIFY_SSL

    def test_getlist(self):
        settings_manager = self.get_instance
        concurrency = settings_manager.getlist("ITEM_PIPELINES")
        assert concurrency == BaseSettings.ITEM_PIPELINES
