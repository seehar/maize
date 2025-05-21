import click

from .code_generate import CodeGenerate


@click.group()
def cli():
    pass


@cli.command()
@click.argument("project_name")
def create(project_name: str):
    """生成项目结构"""
    print(f"{project_name} 成功生成")
    CodeGenerate().generate(project_name)
