import shutil

from maize.command.code_generate import CodeGenerate


class TestCodeGenerate:
    def test_generate(self):
        code_generate = CodeGenerate()
        code_generate.generate("baidu_spider", "https://www.baidu.com")
        # 删除创建的目录
        shutil.rmtree("baidu_spider")
