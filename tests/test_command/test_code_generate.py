from maize.command.code_generate import CodeGenerate


class TestCodeGenerate:
    def test_generate(self):
        code_generate = CodeGenerate()
        code_generate.generate("baidu_spider")
