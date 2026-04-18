---
name: build-fix
description: 快速排查并修复构建/测试错误
allowed-tools: Bash(uv run ruff *) Bash(uv run mypy *) Bash(uv run pytest *) Bash(uv run pre-commit run *)
---

按顺序排查并修复 maize 项目的构建错误 $ARGUMENTS：

1. 运行 `uv run ruff check maize/`，如有错误先尝试 `uv run ruff check --fix maize/` 自动修复
2. 运行 `uv run mypy maize/`，分析并修复类型错误
3. 运行 `uv run pytest -q tests/`，分析并修复测试失败
4. 全部通过后运行 `uv run pre-commit run --all-files` 做最终验证
5. 报告修复结果
