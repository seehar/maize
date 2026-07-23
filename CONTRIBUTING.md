# 贡献指南

欢迎为 maize 贡献代码！无论是 Bug 报告、功能建议、文档改进还是代码提交，都非常感谢。

## 行为准则

请保持友善和尊重。技术讨论聚焦于问题本身，避免人身攻击。

## 如何贡献

### 报告 Bug

1. 在 [Issues](https://github.com/seehar/maize/issues) 搜索是否已有相同问题
2. 创建新 Issue，包含以下信息：
   - maize 版本（`pip show maize`）
   - Python 版本、操作系统
   - 最小复现代码（越短越好）
   - 完整的错误堆栈
   - 期望行为 vs 实际行为

### 提交功能建议

1. 先开 Issue 说明你的想法和动机
2. 等待讨论确认方向后再开始编码
3. 功能应符合框架定位：
   - **Lite 模式**保持轻量，不引入中间件链/调度器/多下载器
   - **Classic 模式**适合中间件、管道、分布式等复杂功能

### 改进文档

文档源码在 `docs/`，基于 mkdocs-material。发现问题直接提 PR 即可。

## 开发环境搭建

### 前置要求

- Python 3.10+
- [uv](https://docs.astral.sh/uv/)（推荐）或 pip

### 步骤

```shell
# 克隆仓库
git clone https://github.com/seehar/maize.git
cd maize

# 安装依赖（含开发、测试、文档依赖）
uv sync --all-extras

# 安装 pre-commit 钩子
uv run pre-commit install
```

### 验证环境

```shell
# 运行测试
uv run pytest --cov=./maize --cov-report=html

# 代码检查
uv run ruff check maize/
uv run mypy maize/
```

## 开发规范

### 代码风格

- 使用 **ruff** 进行 lint 和格式化，配置在 `pyproject.toml`
- 行宽 120 字符
- 类型标注：公共 API 必须标注，内部函数建议标注
- 全限定名导入，禁止通配符 `from x import *`
- 外部类在文件顶部 import，不使用内联 import

### 异步代码

- 所有 IO 操作必须使用 `async/await`，禁止在 async 函数中调用阻塞 API
- `aiohttp.ClientSession` 必须复用，禁止在循环中反复创建
- 连接和 session 必须在使用后正确关闭（推荐 `async with`）

### 双模式边界

maize 有 Lite 和 Classic 两种模式，修改时注意边界：

| 模块 | 说明 |
|------|------|
| `maize/aio/lite/` | Lite 模式，保持轻量，禁止引入中间件/管道/调度器 |
| `maize/aio/classic/` | Classic 模式，完整功能 |
| `maize/base/`、`maize/common/` | 共享模块，修改时需同时验证两种模式 |

### 测试

- 测试文件放在 `tests/` 下，按模块组织
- 使用 `pytest-asyncio`，测试函数加 `@pytest.mark.asyncio`
- 新功能必须有测试覆盖
- 测试中禁止内联 import（ruff `PLC0415`），使用顶层 import

### 安全

- 不要把密钥、固定环境地址、生产参数硬编码到代码中
- 优先通过环境变量注入
- 详见 `.claude/rules/security.md`

## 提交规范

### Commit Message 格式

```
<type>(<scope>): <subject>

<body>
```

**type**（必选）：

| type | 说明 |
|------|------|
| `feat` | 新功能 |
| `fix` | Bug 修复 |
| `docs` | 文档变更 |
| `style` | 代码格式（不影响功能） |
| `refactor` | 重构（非新增功能也非修复 Bug） |
| `perf` | 性能优化 |
| `test` | 测试相关 |
| `chore` | 构建、工具、依赖等杂项 |
| `ci` | CI 配置 |
| `build` | 版本发布 |

**scope**（可选）：影响的模块，如 `lite`、`middleware`、`docs`、`settings`

**subject**（必选）：简短描述，不超过 50 字符，不加句号

示例：

```
feat(lite): 新增域名级并发限流 per_domain_concurrency
fix(lite): 修复 SIGINT 死锁问题
docs: 修正 priority 方向说明
build: 0.5.0
```

### 提交前检查

```shell
# 确保 pre-commit 通过
uv run pre-commit run --all-files

# 确保测试通过
uv run pytest

# 确保代码检查通过
uv run ruff check
```

### PR 要求

1. **单一职责**：一个 PR 只做一件事，不要混合无关改动
2. **描述清晰**：PR 描述说明改了什么、为什么改、如何测试
3. **测试通过**：CI 必须绿色
4. **文档同步**：如有 API 变更，同步更新文档
5. **CHANGELOG**：如有用户可感知的变更，更新 `CHANGELOG.md`

## 发布流程

发布由维护者执行：

1. 确认 `main` 分支干净，测试通过
2. 更新 `pyproject.toml` 中的 `version`
3. 更新 `CHANGELOG.md`
4. `uv build` + `uv publish`
5. 打 tag：`git tag -a vX.Y.Z -m "vX.Y.Z"`
6. `git push origin main && git push origin vX.Y.Z`

## 许可证

提交的代码默认遵循 [MIT License](LICENSE)。
