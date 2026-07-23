"""
Tests for CodeGenerate, maize_command CLI, and code templates.
"""

from pathlib import Path
from unittest.mock import patch

import click
import pytest
from click.testing import CliRunner

from maize import Item, Spider
from maize.command.code_generate import CodeGenerate
from maize.command.code_template.item_template import ItemTemplate
from maize.command.code_template.spider_template import SpiderTemplate
from maize.command.maize_command import cli


class TestCodeGenerateClassName:
    """Test CodeGenerate._get_class_name."""

    def test_simple_name(self):
        assert CodeGenerate._get_class_name("myspider") == "Myspider"

    def test_snake_case(self):
        assert CodeGenerate._get_class_name("my_spider") == "MySpider"

    def test_multi_word_snake_case(self):
        assert CodeGenerate._get_class_name("baidu_news_spider") == "BaiduNewsSpider"

    def test_single_char(self):
        assert CodeGenerate._get_class_name("a") == "A"

    def test_already_capitalized_parts(self):
        assert CodeGenerate._get_class_name("My_Spider") == "MySpider"


class TestCodeGenerateSpiderTemplate:
    """Test CodeGenerate.get_spider_template."""

    def test_template_contains_class_name(self):
        gen = CodeGenerate()
        with patch("builtins.input", return_value="https://example.com"):
            content = gen.get_spider_template("test_spider")
        assert "TestSpider" in content
        assert "https://example.com" in content

    def test_template_adds_https_prefix(self):
        gen = CodeGenerate()
        with patch("builtins.input", return_value="example.com"):
            content = gen.get_spider_template("test_spider")
        assert "https://example.com" in content

    def test_template_with_explicit_url(self):
        gen = CodeGenerate()
        content = gen.get_spider_template("test_spider", url="https://already.set")
        assert "https://already.set" in content

    def test_template_with_http_url(self):
        gen = CodeGenerate()
        content = gen.get_spider_template("test_spider", url="http://example.com")
        assert "http://example.com" in content


class TestCodeGenerateItemTemplate:
    """Test CodeGenerate.get_item_template."""

    def test_template_contains_class_name(self):
        gen = CodeGenerate()
        content = gen.get_item_template("test_spider")
        assert "TestSpiderItem" in content


class TestCodeGenerateGenerate:
    """Test CodeGenerate.generate creates project files."""

    def test_generate_creates_files(self, tmp_path: Path):
        gen = CodeGenerate()
        project_name = str(tmp_path / "test_spider")
        gen.generate(project_name, url="https://example.com")

        project_path = tmp_path / "test_spider"
        assert project_path.exists()
        assert (project_path / "__init__.py").exists()
        assert (project_path / "test_spider.py").exists()
        assert (project_path / "test_spider_item.py").exists()

    def test_generate_raises_on_existing_dir(self, tmp_path: Path):
        gen = CodeGenerate()
        existing = tmp_path / "existing"
        existing.mkdir()
        with pytest.raises(click.ClickException, match="目录已存在"):
            gen.generate(str(existing), url="https://example.com")


class TestMaizeCommandCli:
    """Test the maize CLI entry point."""

    def test_cli_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "create" in result.output

    def test_create_command_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["create", "--help"])
        assert result.exit_code == 0
        assert "PROJECT_NAME" in result.output

    def test_create_command_creates_project(self, tmp_path: Path):
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=str(tmp_path)):
            with patch("builtins.input", return_value="https://example.com"):
                result = runner.invoke(cli, ["create", "myproject"])
            assert result.exit_code == 0
            assert "成功" in result.output


class TestCodeTemplates:
    """Test that code template files are valid and loadable."""

    def test_spider_template_is_subclass_of_spider(self):
        """SpiderTemplate should inherit from Spider (checked by import)."""
        assert issubclass(SpiderTemplate, Spider)

    def test_item_template_is_subclass_of_item(self):
        assert issubclass(ItemTemplate, Item)

    def test_spider_template_has_start_requests(self):
        assert hasattr(SpiderTemplate, "start_requests")

    def test_spider_template_has_parse(self):
        assert hasattr(SpiderTemplate, "parse")

    def test_item_template_has_field(self):
        assert "field" in ItemTemplate.model_fields
