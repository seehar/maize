"""
代码生成器，根据模板生成 Spider 和 Item 脚手架。
"""

from pathlib import Path

import click

from maize.common.constant import TemplateFile


class CodeGenerate:
    """
    代码生成
    """

    def __init__(self):
        self._code_template_path = Path(__file__).parent / "code_template"

    def generate(self, spider_name: str, url: str | None = None):
        """生成爬虫代码结构"""

        base_path = Path(spider_name)

        if base_path.exists():
            raise click.ClickException("目录已存在！")

        # Use the directory name for file naming, not the full path
        dir_name = base_path.name
        files = {
            base_path / "__init__.py": "",
            base_path / f"{dir_name}.py": self.get_spider_template(dir_name, url),
            base_path / f"{dir_name}_item.py": self.get_item_template(dir_name),
        }

        base_path.mkdir(parents=True, exist_ok=True)

        for file_path, content in files.items():
            file_path.write_text(content, encoding="utf-8")

        click.echo(f"✅ 项目 {spider_name} 创建成功！")

    def get_spider_template(self, spider_name: str, url: str | None = None) -> str:
        """
        获取 Spider 模板代码。

        :param spider_name: Spider 名称（蛇形命名）
        :param url: 目标 URL，为 None 时交互式输入
        :return: Spider 代码字符串
        """
        if not url:
            url = input("目标网站：")

        if not url.startswith("http"):
            url = f"https://{url}"

        spider_template = self._get_template_file_content(TemplateFile.SPIDER)
        return spider_template.replace("SpiderTemplate", self._get_class_name(spider_name)).replace("url_template", url)

    def get_item_template(self, spider_name: str) -> str:
        """
        获取 Item 模板代码。

        :param spider_name: Spider 名称（蛇形命名）
        :return: Item 代码字符串
        """
        template = self._get_template_file_content(TemplateFile.ITEM)
        return template.replace("ItemTemplate", f"{self._get_class_name(spider_name)}Item")

    def _get_template_file_content(self, template: TemplateFile) -> str:
        with open(self._code_template_path / template.value, encoding="utf-8") as f:
            return f.read()

    @staticmethod
    def _get_class_name(spider_name: str):
        """
        将蛇形命名转换为帕斯卡命名。

        :param spider_name: 蛇形命名的 Spider 名称
        :return: 帕斯卡命名的类名
        """
        spider_name_split = spider_name.split("_")
        class_name_list = []
        for name in spider_name_split:
            class_name_list.append(name.capitalize())
        return "".join(class_name_list)
