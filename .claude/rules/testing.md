# 测试规则

## 测试覆盖率

1. **新增代码必须包含测试**
   - 核心模块（`maize/core/`, `maize/aio/`）必须有测试
   - 公共 API 必须有测试覆盖

2. **测试文件命名**
   - `test_*.py` - 测试文件
   - 与被测模块结构一致：`tests/test_core/test_stats/test_stats_collector.py`

## 异步测试

1. **使用 pytest-asyncio**
   ```python
   import pytest

   @pytest.mark.asyncio
   async def test_async_function():
       result = await async_function()
       assert result is not None
   ```

2. **事件循环策略**
   - 测试使用 `pytest.mark.asyncio` 时确保正确设置 event loop policy
   - 避免在测试中创建嵌套事件循环

## Mock 策略

1. **HTTP 请求**
   - 使用 `pytest-httpx` 或 `aiohttp.test_utils` mock HTTP 响应
   - 不要真实发起网络请求

2. **数据库**
   - 测试使用内存数据库或 mock
   - 不污染生产数据
