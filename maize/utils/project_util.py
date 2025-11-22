import sys
from collections.abc import Callable
from importlib import import_module
from pathlib import Path
from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from maize.settings import SpiderSettings


def _get_closest(path: str = ".") -> str:
    """
    获取最近的 settings.py 路径
    :param path:
    :return:
    """
    return str(Path(path).resolve())


def _init_env():
    """
    初始化环境变量
    :return:
    """
    closest = _get_closest()
    if closest:
        project_dir = str(Path(closest).parent)
        sys.path.append(project_dir)


def get_settings(
    settings: str = "maize.SpiderSettings",
) -> "SpiderSettings":
    """
    获取settings配置文件
    :param settings:
    :return:
    """
    _init_env()
    return load_class(settings)()


def load_class(_path: Union[str, Callable]):
    """
    动态导入类
    :param _path:
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
        raise NameError(f"Module {module_name!r} does not define any object class named {class_name!r}") from None
