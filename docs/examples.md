# 示例索引

`examples/` 目录包含多个完整示例，覆盖 Lite、Classic、中间件、RPA 等场景。

## 基础示例

### Lite 爬虫基础

**文件**：[`lite_spider_example.py`](https://github.com/seehar/maize/blob/main/examples/lite_spider_example.py)

最小可运行的 Lite 爬虫，抓取 httpbin.org 三个页面，展示 `start_requests` + `parse` 基本结构。

```python
class SimpleLiteSpider(LiteSpider):
    async def start_requests(self):
        yield Request(url="https://httpbin.org/get")
        yield Request(url="https://httpbin.org/json")

    async def parse(self, response: Response):
        self.logger.info(f"Status: {response.status}, URL: {response.url}")
```

### Classic 爬虫最简示例

**文件**：[`simple_spider.py`](https://github.com/seehar/maize/blob/main/examples/simple_spider.py)

最简 Classic 爬虫，百度首页抓取，展示 `SpiderSettings` 对象配置。

### 装饰器启动入口

**文件**：[`decorator_spider.py`](https://github.com/seehar/maize/blob/main/examples/decorator_spider.py)

使用 `@SpiderEntry` 装饰器启动爬虫的替代方式。

## 完整项目示例

### 百度爬虫完整项目

**目录**：[`baidu_spider/`](https://github.com/seehar/maize/blob/main/examples/baidu_spider/)

完整项目结构，包含 Item 定义、自定义 Pipeline、多爬虫、独立配置文件：

```text
baidu_spider/
├── spiders/
│   ├── __init__.py
│   └── baidu_spider.py    # 爬虫实现
├── items.py               # Item 定义
├── pipeline.py            # 自定义 Pipeline
├── run.py                 # 启动入口
└── logger_util.py         # 自定义日志
```

这个示例展示了 Classic 模式的完整工作流：

1. 定义 `BaiduItem`（带 `__table_name__`）
2. 实现分页抓取（`parse` → `parse_page` → `parse_detail`）
3. 自定义 Pipeline 处理数据
4. 使用 `CrawlerProcess` 启动

## 中间件示例

### 自定义中间件完整示例

**文件**：[`middleware_example.py`](https://github.com/seehar/maize/blob/main/examples/middleware_example.py)

覆盖三层中间件的完整示例：

- `CustomUserAgentMiddleware`（下载器中间件）—— 为请求添加自定义 UA
- `RequestLoggingMiddleware`（下载器中间件）—— 记录所有请求和响应
- `DepthLimitMiddleware`（爬虫中间件）—— 限制爬取深度
- `ItemCountMiddleware`（管道中间件）—— 统计 Item 数量

展示了中间件的 `process_request`、`process_response`、`process_spider_input`、`process_spider_output` 等钩子的完整用法。

## RPA 示例

### 百度 RPA 爬虫

**文件**：[`rpa_baidu_spider.py`](https://github.com/seehar/maize/blob/main/examples/rpa_spdier/rpa_baidu_spider.py)

使用 Playwright 下载器抓取百度搜索结果，展示 RPA 基本配置。

### RPA + 接口拦截

**文件**：[`rpa_baidu_url_regiexes_spider.py`](https://github.com/seehar/maize/blob/main/examples/rpa_spdier/rpa_baidu_url_regiexes_spider.py)

使用 `url_regexes` 拦截 XHR/Fetch 请求，直接从 API 响应提取数据，绕过页面解析。

### RPA + 下载文件

**文件**：[`rpa_dowload_spider.py`](https://github.com/seehar/maize/blob/main/examples/rpa_spdier/rpa_dowload_spider.py)

使用 RPA 下载文件的完整流程。

### RPA + 代理

**文件**：[`rpa_proxy_spider.py`](https://github.com/seehar/maize/blob/main/examples/rpa_spdier/rpa_proxy_spider.py)

RPA 爬虫配合代理 IP 使用。

### 京东 RPA 爬虫

**文件**：[`rpa_jd_spider.py`](https://github.com/seehar/maize/blob/main/examples/rpa_spdier/rpa_jd_spider.py)

抓取京东商品页面，展示更复杂的 RPA 场景。

### Patchright RPA 爬虫

**目录**：[`patchright_rpa_spider/`](https://github.com/seehar/maize/blob/main/examples/rpa_spdier/patchright_rpa_spider/)

使用 Patchright（反检测 Playwright 分支）的百度爬虫，适合反爬较强的网站。

## 暂停与继续

### 暂停继续爬虫

**目录**：[`pause_and_proceed_spider/`](https://github.com/seehar/maize/blob/main/examples/pause_and_proceed_spider/)

展示 `pause_spider()` 和 `proceed_spider()` 的用法：

- 按条件暂停所有请求
- 按优先级暂停/继续（`pause_spider(lte_priority=5)`）
- 恢复所有请求

---

## 如何运行示例

```shell
# 克隆仓库
git clone https://github.com/seehar/maize.git
cd maize

# 安装依赖（根据示例选择 extras）
uv sync --all-extras

# 运行示例
uv run python examples/lite_spider_example.py
uv run python examples/simple_spider.py
uv run python examples/middleware_example.py
```

RPA 示例需要额外安装浏览器驱动：

```shell
playwright install
```

## 下一步

- [架构概览](architecture.md) — 理解框架结构
- [快速上手](quick_start.md) — 跟着教程写爬虫
- [FAQ](faq.md) — 常见问题解答
