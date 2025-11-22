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

        files = {
            base_path / "__init__.py": "",
            base_path / f"{spider_name}.py": self.get_spider_template(spider_name, url),
            base_path / f"{spider_name}_item.py": self.get_item_template(spider_name),
        }

        base_path.mkdir(parents=True, exist_ok=True)

        for file_path, content in files.items():
            file_path.write_text(content, encoding="utf-8")

        click.echo(f"✅ 项目 {spider_name} 创建成功！")

    def get_spider_template(self, spider_name: str, url: str | None = None) -> str:
        if not url:
            url = input("目标网站：")

        if not url.startswith("http"):
            url = f"https://{url}"

        spider_template = self._get_template_file_content(TemplateFile.SPIDER)
        return spider_template.replace("SpiderTemplate", self._get_class_name(spider_name)).replace("url_template", url)

    def get_item_template(self, spider_name: str) -> str:
        template = self._get_template_file_content(TemplateFile.ITEM)
        return template.replace("ItemTemplate", f"{self._get_class_name(spider_name)}Item")

    def _get_template_file_content(self, template: TemplateFile) -> str:
        with open(self._code_template_path / template.value, encoding="utf-8") as f:
            return f.read()

    @staticmethod
    def _get_class_name(spider_name: str):
        spider_name_split = spider_name.split("_")
        class_name_list = []
        for name in spider_name_split:
            class_name_list.append(name.capitalize())
        return "".join(class_name_list)
