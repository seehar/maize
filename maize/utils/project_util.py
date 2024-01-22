import os
import sys
import typing
from importlib import import_module

from maize.core.settings.settings_manager import SettingsManager


if typing.TYPE_CHECKING:
    from maize.core.spider.spider import Spider


def _get_closest(path: str = ".") -> str:
    """
    获取最近的 settings.py 路径
    :param path:
    :return:
    """
    return os.path.abspath(path)


def _init_env():
    """
    初始化环境变量
    :return:
    """
    closest = _get_closest()
    if closest:
        project_dir = os.path.dirname(closest)
        sys.path.append(project_dir)


def get_settings(settings: str = "maize.settings.default_settings") -> SettingsManager:
    """
    获取settings配置文件
    :param settings:
    :return:
    """
    _settings = SettingsManager()
    _init_env()
    _settings.set_settings(settings)
    return _settings


def merge_settings(spider: "Spider", settings: SettingsManager):
    """
    合并配置文件

    @type spider: Spider
    @param spider:
    @param settings:
    @return:
    """
    if hasattr(spider, "custom_settings"):
        custom_settings = getattr(spider, "custom_settings")
        settings.update_values(custom_settings)


def load_class(_path: str | typing.Callable):
    """
    动态导入类
    @param _path:
    @return:
    """
    if not isinstance(_path, str):
        if callable(_path):
            return _path

        raise TypeError(f"args expected string or object, got {type(_path)}")

    module_name, class_name = _path.rsplit(".", 1)
    module = import_module(module_name)
    try:
        return getattr(module, class_name)
    except AttributeError:
        raise NameError(
            f"Module {module_name!r} does not define any object class named {class_name!r}"
        )
