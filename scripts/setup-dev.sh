#!/bin/bash
# 开发环境设置脚本

set -e

echo "🚀 开始设置 Maize 开发环境..."

# 检查是否安装了 uv
if ! command -v uv &> /dev/null; then
    echo "❌ uv 未安装，请先安装 uv: https://github.com/astral-sh/uv"
    exit 1
fi

echo "✅ uv 已安装"

# 安装依赖
echo "📦 安装项目依赖..."
uv sync --all-extras --dev

# 安装 pre-commit 钩子
echo "🪝 设置 pre-commit 钩子..."
uv run pre-commit install

echo ""
echo "✨ 开发环境设置完成！"
echo ""
echo "可用命令："
echo "  make format        - 格式化代码"
echo "  make lint          - 运行代码检查"
echo "  make test          - 运行测试"
echo "  make all           - 运行所有检查"
echo ""
echo "📚 更多信息请查看: docs/dev/formatting.md"
