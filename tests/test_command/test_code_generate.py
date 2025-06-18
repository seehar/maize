import shutil

import click
import pytest

from maize.command.code_generate import CodeGenerate


class TestCodeGenerate:
    def test_generate(self):
        code_generate = CodeGenerate()
        code_generate.generate("baidu_spider", "https://www.baidu.com")
        # 删除创建的目录
        shutil.rmtree("baidu_spider")

    def test_generate_project_url_no_http(self):
        code_generate = CodeGenerate()
        code_generate.generate("baidu_spider_url_no_http", "www.baidu.com")
        # 删除创建的目录
        shutil.rmtree("baidu_spider_url_no_http")

    def test_generate_no_remove_dir(self):
        code_generate = CodeGenerate()
        with pytest.raises(click.ClickException):
            for _ in range(2):
                code_generate.generate("test_generate_no_remove_dir", "https://www.baidu.com")
        shutil.rmtree("test_generate_no_remove_dir")
