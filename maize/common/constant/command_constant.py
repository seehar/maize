"""
命令行模板文件常量。

定义 ``maize startproject`` 等命令生成项目骨架时使用的模板文件名。
"""

from enum import Enum, unique


@unique
class TemplateFile(Enum):
    """
    项目模板文件枚举。

    每个成员的值对应 ``maize/templates/`` 下的模板文件名，
    供代码生成命令读取并渲染。
    """

    SPIDER = "spider_template.py"
    PIPELINE = "pipeline_template.py"
    ITEM = "item_template.py"
    SETTING = "settings_template.py"
