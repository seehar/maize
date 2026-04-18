# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 在此代码仓库中工作时提供指导。
每次完成任务前，思考下是否有更优雅的实现方式，是否有更清晰的代码结构，是否有更合理的命名，是否有更全面的测试覆盖。保持代码质量和可维护性是我们共同的责任。

## 环境与常用命令

```bash
# 安装依赖
uv sync --all-groups

# 代码检查（不修改）
uv run ruff check maize examples tests

# 格式化
uv run ruff format maize examples tests

# 类型检查
uv run mypy maize

# 运行测试
uv run pytest -q tests/

# 运行单个测试
uv run pytest tests/path/to/test_file.py::test_function_name

# pre-commit 钩子
uv run pre-commit run --all-files

# 项目 Makefile（等效快捷方式）
make install  make format  make lint  make type-check  make test
```

## 架构概览

### 爬虫模式

Maize 是一个 Python 爬虫框架，项目存在两种爬虫模式：

**1. Classic 模式** (`from maize.aio.classic.spider.spider import Spider`)
- 完整功能的异步爬虫，使用 CrawlerProcess 运行
- 支持中间件、管道、调度器
- 示例：`maize/aio/classic/spider/spider.py`

**2. Lite 模式** (`from maize.aio.lite.spider.lite_spider import LiteSpider`)
- 轻量级爬虫，适合简单场景
- 示例：`maize/aio/lite/spider/lite_spider.py`

### 核心模块

- `maize/aio/classic/`：完整版爬虫实现（downloader, spider, scheduler, middleware, pipeline, crawler）
- `maize/aio/lite/`：轻量版爬虫实现
- `maize/base/`：基类定义（interface, spider, downloader, scheduler, middleware, pipeline）
- `maize/common/`：公共组件（http, items, model, constant, downloader）
- `maize/core/`：核心组件（engine, processor, stats, task）
- `maize/command/`：CLI 命令实现
- `maize/exceptions/`：异常定义
- `maize/factory/`：工厂模式组件
- `maize/pipelines/`：数据管道实现
- `maize/middlewares/`：中间件实现
- `maize/utils/`：工具模块
- `maize/settings/`：配置类

### 入口与 CLI

框架入口：`maize/__init__.py`
命令行：`maize.command.maize_command:cli`

## 代码规范

- **Import**: `maize` 为已知第一方包；**禁止在代码中间写 import 语句，默认放在文件顶部**
- **Lint/Format**: ruff（已配置 pyproject.toml），中文注释不触发 RUF001/002/003 警告
- **类型检查**: mypy，模块级忽略 `tests.*`，中文 identifier 不报错
- **Commit**: 遵循 Conventional Commits，格式为 `type: 简短中文描述`
- **IDE 诊断**: 代码必须无任何 IDE 错误或警告，提交前使用 IDE 内置诊断确认文件状态
- **类型检查**: 尽量避免使用 `cast` 绕过类型检查，必要时添加详细注释说明原因

## 配置即代码

详细规范位于 `.claude/` 目录:
- `rules/` — 安全、测试、编码风格规则
- `agents/` — 专用子代理 (planner, code-reviewer, build-error-resolver)
- `commands/` — Slash 命令 (plan, code-review, build-fix)
- `settings.local.json` — 权限白名单与 Claude Code hooks（编辑后自动 ruff format）

pre-commit hooks 配置见 `.pre-commit-config.yaml`。

详细规范: `AGENTS.md`
