from enum import Enum, unique


@unique
class TemplateFile(Enum):
    SPIDER = "spider_template.py"
    PIPELINE = "pipeline_template.py"
    ITEM = "item_template.py"
    SETTING = "settings_template.py"
