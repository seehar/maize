# FAQ 与故障排查

## 常见问题

### Lite 和 Classic 怎么选？

参见 [使用前必读 - 选择爬虫模式](use/before_use.md)。简单判断：

- **选 Lite**：只需抓取页面/API，不想配置文件，单文件即跑
- **选 Classic**：需要中间件（UA 轮换、代理池）、多管道入库、分布式、RPA

### maize 和 Scrapy 有什么区别？

| 维度 | maize | Scrapy |
|------|-------|--------|
| 异步 | 原生 asyncio 全链路 | Twisted（可集成 asyncio） |
| 轻量入口 | Lite 模式单文件即跑 | 需 startproject 脚手架 |
| 浏览器自动化 | 内置 Playwright + Patchright | 需第三方插件 |
| 配置 | Pydantic v2 强类型 | dict 风格 |

### 为什么用 Pydantic v2 而不是 dataclass？

强类型校验、嵌套配置、环境变量/JSON/YAML/TOML 多来源自动加载、序列化。代价是 Pydantic v2 的字段覆盖规则更严格（见下）。

### 支持 Python 3.9 吗？

不支持。maize 使用了 `str | None`（PEP 604）等 3.10+ 语法，最低要求 Python 3.10。

---

## 安装与依赖

### `pip install maize[rpa]` 后浏览器没启动

RPA 依赖需要额外安装浏览器驱动：

```shell
pip install maize[rpa]
playwright install        # 下载 Chromium/Firefox/WebKit
```

Patchright 用户还需要：

```shell
patchright install chromium
```

### `ImportError: No module named 'aiomysql'`

MySQL Pipeline 需要 `mysql` 扩展：

```shell
pip install maize[mysql]
```

### `ImportError: No module named 'redis'`

Redis 分布式功能需要 `redis` 扩展：

```shell
pip install maize[redis]
```

---

## Pydantic v2 相关

### `PydanticUserError: Field defined on a base class was overridden by a non-annotated attribute`

在 `SpiderSettings` 子类中覆盖父类字段时，**必须带类型注解**。

```python
# ❌ 错误：缺少类型注解
class Settings(SpiderSettings):
    project_name = "my_spider"

# ✅ 正确：带类型注解
class Settings(SpiderSettings):
    project_name: str = "my_spider"
```

### Item 的 Field 也需要类型注解吗？

需要。Pydantic v2 要求所有字段都有类型注解：

```python
# ❌ 错误
class MyItem(Item):
    title = Field()

# ✅ 正确
class MyItem(Item):
    title: str = Field()
```

---

## 运行时错误

### `RuntimeError: Session is closed`

aiohttp 的 `ClientSession` 在关闭后又被使用。常见原因：

1. Lite 爬虫在 `on_close` 中手动关闭了 session（框架已自动管理）
2. Classic 爬虫的 `downloader.close()` 被提前调用

**解决**：不要手动管理 session 生命周期，框架在 `spider.close()` 时自动处理。

### `RuntimeError: Event loop is closed`（Windows）

Windows 的 `ProactorEventLoop` 在某些场景下关闭时抛此异常。

**解决**：在 `main()` 末尾添加：

```python
import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
```

### Lite 爬虫 Ctrl+C 后卡住不退出

已在 v0.5.0 修复（commit a765b7c）。如果仍遇到，请升级到最新版本：

```shell
pip install --upgrade maize
```

### 请求被去重，但确实需要重复抓取

两种方式跳过去重：

```python
# 方式一：整个 Spider 关闭去重（适合轮询监控）
class PollingSpider(LiteSpider):
    dedup = False

# 方式二：单个请求跳过（适合个别 URL 重复抓）
yield Request(url="https://example.com", meta={"dont_filter": True})
```

### POST + JSON 请求被误判为重复

v0.5.0 已修复 `Request.hash` 缺失 `json` 字段的问题（commit a765b7c）。升级后即可。

---

## 中间件与 Pipeline

### 中间件没有生效

检查优先级配置：

```python
settings.middleware.downloader_middlewares = {
    "my_project.middleware.CustomMiddleware": 600,  # 自定义中间件建议 600-999
}
settings.middleware.enable_builtin_middlewares = True  # 确保没被关闭
```

优先级范围建议：0-99 系统保留，100-299 内置，300-599 第三方，600-999 自定义。

### Pipeline 的 `process_item` 没有被调用

检查以下几点：

1. `parse` 中 `yield Item`（不是 `yield dict`，dict 不走 Pipeline）
2. Pipeline 已在配置中注册：`settings.pipeline.pipelines = ["my_module.MyPipeline"]`
3. `process_item` 返回 `True` 表示成功（返回 `False` 会触发重试）

### MySQL Pipeline 跳过了我的 Item

`__table_name__` 为空的 Item 会被 MySQL Pipeline 跳过：

```python
class MyItem(Item):
    __table_name__ = "my_table"  # 必须设置
    title: str = Field()
```

---

## RPA / 浏览器自动化

### 页面没有完全渲染就返回了

调整等待策略：

```python
settings.rpa.wait_until = "networkidle"  # 默认 domcontentloaded
settings.rpa.render_time = 3  # 额外等待 3 秒
```

### 被网站检测到是自动化工具

1. 使用 `PatchrightDownloader`（反检测能力更强）
2. 确认 `use_stealth_js=True`（默认开启）
3. 设置真实的 User-Agent

```python
from maize import SpiderSettings, SpiderDownloaderEnum

settings = SpiderSettings(downloader=SpiderDownloaderEnum.PATCHRIGHT.value)
settings.rpa.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ..."
```

### 如何拦截 XHR/Fetch 请求

使用 `url_regexes` 配置：

```python
settings.rpa.url_regexes = [r"/api/list", r"/api/detail"]
settings.rpa.url_regexes_save_all = False  # 只保存匹配的
```

详见 [examples/rpa_spdier/rpa_baidu_url_regiexes_spider.py](https://github.com/seehar/maize/blob/main/examples/rpa_spdier/rpa_baidu_url_regiexes_spider.py)。

---

## 分布式

### 多台机器运行时重复抓取

确保所有机器使用相同的 Redis 配置和 `key_prefix`：

```python
settings.is_distributed = True
settings.redis.host = "192.168.1.100"
settings.redis.key_prefix = "maize"  # 所有机器必须一致
```

### Redis 连接失败

1. 检查 `settings.redis.host` / `port` / `password`
2. 确认 Redis 服务可达：`redis-cli -h <host> -p <port> ping`
3. 如果 Redis 有密码，检查 `settings.redis.password`

---

## 日志

### 如何使用 loguru 替代默认日志

```python
# logger_util.py
import logging
import sys
from loguru import logger as loguru_logger

class InterceptHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.logger = loguru_logger
        self.logger.remove()
        self.logger.add(sys.stdout, level="DEBUG")

    def emit(self, record: logging.LogRecord):
        self.logger.opt(depth=6, exception=record.exc_info).log(
            record.levelname, record.getMessage()
        )
```

配置中指定：

```python
settings = SpiderSettings(logger_handler="logger_util.InterceptHandler")
```

### 日志重复输出

LiteCrawler 复用 `spider.logger`，不要额外创建 logger。Classic 模式确保没有重复注册 handler。

---

## 性能

### 如何提高采集速度

1. 增加 `concurrency`：`settings = SpiderSettings(concurrency=20)`
2. 使用请求优先级：`yield Request(url=..., priority=1)`（数值越小越优先）
3. 减少超时等待：`settings.request.request_timeout = 10`
4. 关闭不需要的资源加载（RPA）：`settings.rpa.skip_resource_types = ["image", "media", "font"]`

### 如何避免被封禁

1. 降低并发：`concurrency=1` + `per_domain_concurrency=1`（Lite）
2. 设置随机等待：`settings.request.random_wait_time = (1, 3)`（Classic）
3. 使用代理池（Classic 中间件实现）
4. 轮换 User-Agent（`UserAgentMiddleware`）
5. 使用 Patchright 下载器降低检测风险

---

## 更多帮助

- [架构概览](architecture.md) — 理解框架结构
- [示例索引](examples.md) — 完整代码示例
- [GitHub Issues](https://github.com/seehar/maize/issues) — 提交问题
