---
name: code-review
description: 对当前改动或指定文件进行代码审查
allowed-tools: Bash(uv run ruff *) Bash(uv run mypy *) Bash(git diff *)
---

对以下目标进行代码审查: $ARGUMENTS

如果未指定文件，审查当前 `git diff` 中的所有变更。

## 审查步骤

1. 运行 `uv run ruff check` 和 `uv run mypy` 检查目标文件
2. 阅读代码，按 `.claude/rules/coding-style.md` 中的检查清单逐项审查
3. 重点关注：
   - 异步代码是否正确使用 await
   - Spider 是否只负责抓取（不写数据库、不操作 Redis）
   - 类型注解是否完整
   - 是否有安全风险（参照 `.claude/rules/security.md`）
4. 按严重程度（Critical > Warning > Info）输出审查结果
