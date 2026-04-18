# 编码风格规则

## 技术栈约束

- Python 3.10+
- asyncio / aiohttp / httpx
- 常见爬虫组件（代理池 / 任务队列 / Redis / MongoDB / MySQL）
- 注释为 reStructuredText 格式
  示例：
  ```python
  def crawl(self, url: str) -> Response:
      """
      发起爬取请求并返回响应。

      :param url: 目标 URL
      :return: 响应对象
      """
  ```

---

## Import 规范

1. **禁止在代码中间写 import 语句**
   - 所有 import 必须放在文件顶部
   - 唯一例外：类型检查时的条件 import

2. **Import 顺序（ruff check --fix 自动处理）**
   - 标准库
   - 第三方库
   - 内部模块 (`maize`)

3. **绝对导入优先**
   - 使用 `from maize.common.http import Request` 而非相对导入

## 命名规范

1. **类名**: `PascalCase` (e.g., `Spider`, `LiteSpider`)
2. **函数/方法/变量**: `snake_case` (e.g., `parse_response`, `request_count`)
3. **常量**: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_TIMEOUT`, `MAX_RETRIES`)
4. **模块名**: `snake_case` (e.g., `stats_collector.py`)

## 类型注解

1. **公共 API 必须有类型注解**
   ```python
   def parse_response(response: Response) -> list[Item]:
       ...
   ```

2. **复杂泛型添加注释说明**
   ```python
   # dict: url -> (name, age)
   def get_user_info() -> dict[str, tuple[str, int]]:
       ...
   ```

## 文档字符串

1. **公共类/函数添加 docstring（reStructuredText 格式）**
   ```python
   def crawl(self, url: str) -> Response:
       """
       发起爬取请求并返回响应。

       :param url: 目标 URL
       :return: 响应对象
       """
   ```

2. **简短方法可省略 docstring**，但 `__init__` 除外

---

## 强制检查项

### 设计原则

- [ ] 单一职责原则（SRP）
- [ ] 开闭原则（OCP）
- [ ] 依赖倒置原则（DIP）
- [ ] 高内聚低耦合

---

### 代码质量

- [ ] 函数超过 **80 行 → 警告**
- [ ] 类职责过多 → **严重问题**
- [ ] 重复代码
- [ ] 魔法值
- [ ] 硬编码
- [ ] 全局变量滥用
- [ ] mutable 默认参数
- [ ] 空指针风险（None 判断）
- [ ] 吞异常
- [ ] 日志不规范
- [ ] 资源未关闭（文件 / session / 连接）
- [ ] 不安全的 `eval / exec`
- [ ] 不规范的 `__eq__ / __hash__`（如果存在）

---

### 爬虫架构规范

- [ ] Spider **只负责抓取，不允许写复杂业务逻辑**
- [ ] Parser **只负责解析**
- [ ] Pipeline **只负责数据处理 / 存储**
- [ ] 不允许 Spider 直接写数据库
- [ ] 不允许 Spider 直接操作 Redis / MQ
- [ ] 配置必须放在 settings / config 中

---

### 并发与异步

- [ ] asyncio 任务是否正确 `await`
- [ ] 是否存在 **阻塞 IO**
- [ ] 不允许在 async 函数中使用 `requests`
- [ ] aiohttp session 是否复用
- [ ] 连接是否正确关闭

---

### 爬虫性能

- [ ] 循环内 HTTP 请求
- [ ] 循环内数据库写入
- [ ] 重复抓取
- [ ] 未做去重
- [ ] 未设置 timeout
- [ ] 未设置 retry
- [ ] 未设置并发限制
- [ ] 未设置速率限制

---

### 反爬与稳定性

- [ ] 是否支持代理
- [ ] 是否支持失败重试
- [ ] 是否支持断点续爬
- [ ] 是否处理 403 / 429
- [ ] 是否处理验证码

---

### 安全

- [ ] URL 拼接风险
- [ ] 参数未校验
- [ ] SSRF 风险
- [ ] Cookie / Token 泄露

---

## 代码审查检查项

- [ ] 无未使用的 import
- [ ] 无 `print` 语句（使用 `loguru` 或 `logging`）
- [ ] 无硬编码的魔法数字
- [ ] 异常处理完整
- [ ] 异步函数正确使用 `await`
- [ ] 类型注解完整
