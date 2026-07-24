"""
maize 命令行入口，基于 click 提供 CLI 命令。
"""

import click

from .code_generate import CodeGenerate


@click.group()
def cli():
    """
    maize 命令行工具入口。
    """
    pass


@cli.command()
@click.argument("project_name")
def create(project_name: str):
    """生成项目结构"""
    print(f"{project_name} 成功生成")
    CodeGenerate().generate(project_name)
