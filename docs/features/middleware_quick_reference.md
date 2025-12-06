# Middleware Quick Reference

## 快速开始

### 1. 使用内置中间件

```python
from maize import Spider

class MySpider(Spider):
    custom_settings = {
        'middleware': {
            'downloader_middlewares': {
                'maize.middlewares.downloader.UserAgentMiddleware': 100,
            }
        }
    }
```

### 2. 创建自定义中间件

```python
from maize.middlewares import DownloaderMiddleware

class MyMiddleware(DownloaderMiddleware):
    async def process_request(self, request, spider):
        return request
```

## 内置中间件速查

### 下载器中间件

| 中间件 | 功能 | 配置 |
|:------|:-----|:----|
| `UserAgentMiddleware` | 轮换 UA | `user_agent_list`, `user_agent_mode` |
| `DefaultHeadersMiddleware` | 默认请求头 | `default_headers` |
| `RetryMiddleware` | 请求重试 | `max_retry_count`, `retry_http_codes` |

### 爬虫中间件

| 中间件 | 功能 | 配置 |
|:------|:-----|:----|
| `DepthMiddleware` | 深度限制 | `max_depth` |
| `HttpErrorMiddleware` | HTTP 错误过滤 | `http_error_allowed_codes` |

### 管道中间件

| 中间件 | 功能 | 配置 |
|:------|:-----|:----|
| `ItemValidationMiddleware` | 数据验证 | `required_fields` |
| `ItemCleanerMiddleware` | 数据清洗 | `strip_whitespace`, `remove_html` |

## 中间件方法返回值

### DownloaderMiddleware

| 方法 | 返回值 | 效果 |
|:----|:------|:----|
| `process_request` | `Request` | 继续处理 |
| | `Response` | 跳过下载 |
| | `None` | 丢弃请求 |
| `process_response` | `Response` | 继续处理 |
| | `Request` | 重试请求 |
| | `None` | 丢弃响应 |
| `process_exception` | `Request` | 重试请求 |
| | `Response` | 使用响应 |
| | `None` | 忽略异常 |

### SpiderMiddleware

| 方法 | 返回值 | 效果 |
|:----|:------|:----|
| `process_spider_input` | `None` | 正常 |
| | 抛出异常 | 触发 exception 处理 |
| `process_spider_output` | `AsyncGenerator` | 返回结果 |
| `process_spider_exception` | `AsyncGenerator` | 处理异常 |
| | `None` | 继续传播 |

### PipelineMiddleware

| 方法 | 返回值 | 效果 |
|:----|:------|:----|
| `process_item_before` | `Item` | 继续处理 |
| | `None` | 丢弃 Item |
| `process_item_after` | `Item` | 继续处理 |
| | `None` | 丢弃 Item |

## 优先级指南

| 范围 | 用途 |
|:----|:----|
| 0-99 | 系统保留 |
| 100-299 | 内置中间件 |
| 300-599 | 第三方中间件 |
| 600-999 | 自定义中间件 |

## 执行顺序

### DownloaderMiddleware
- `process_request`: 升序 (100 → 200 → 300)
- `process_response`: 降序 (300 → 200 → 100)
- `process_exception`: 降序 (300 → 200 → 100)

### SpiderMiddleware
- `process_start_requests`: 降序
- `process_spider_input`: 升序
- `process_spider_output`: 降序
- `process_spider_exception`: 降序

### PipelineMiddleware
- `process_item_before`: 升序
- `process_item_after`: 降序

## 常用代码片段

### 添加自定义请求头

```python
async def process_request(self, request, spider):
    request.headers = request.headers or {}
    request.headers['X-Custom'] = 'value'
    return request
```

### 基于状态码重试

```python
async def process_response(self, request, response, spider):
    if response.status == 429:
        return request  # 重试
    return response
```

### 过滤 URL

```python
async def process_spider_output(self, response, result, spider):
    async for item in result:
        if isinstance(item, Request):
            if 'allowed.com' not in item.url:
                continue
        yield item
```

### 验证必填字段

```python
async def process_item_before(self, item, spider):
    if not hasattr(item, 'title') or not item.title:
        return None  # 丢弃
    return item
```

### 清洗数据

```python
async def process_item_before(self, item, spider):
    if hasattr(item, 'title'):
        item.title = item.title.strip()
    return item
```

## 生命周期方法

```python
class MyMiddleware(DownloaderMiddleware):
    async def open(self):
        """初始化资源"""
        self.db = await connect_db()

    async def close(self):
        """清理资源"""
        await self.db.close()
```

## 从 Crawler 初始化

```python
@classmethod
def from_crawler(cls, crawler):
    """推荐的初始化方式"""
    settings = crawler.settings
    custom_param = getattr(settings, 'my_param', default)
    return cls(settings, custom_param=custom_param)
```

## 日志记录

```python
self.logger.debug("Debug message")
self.logger.info("Info message")
self.logger.warning("Warning message")
self.logger.error("Error message")
```

## 完整示例

```python
from maize.middlewares import DownloaderMiddleware

class CompleteMiddleware(DownloaderMiddleware):
    def __init__(self, settings=None, custom_param=None):
        super().__init__(settings)
        self.custom_param = custom_param

    @classmethod
    def from_crawler(cls, crawler):
        param = getattr(crawler.settings, 'custom_param', 'default')
        return cls(crawler.settings, custom_param=param)

    async def open(self):
        self.logger.info("Middleware opened")

    async def process_request(self, request, spider):
        self.logger.debug(f"Processing: {request.url}")
        return request

    async def process_response(self, request, response, spider):
        self.logger.debug(f"Response: {response.status}")
        return response

    async def close(self):
        self.logger.info("Middleware closed")
```

---

更多信息请参考：
- [完整文档](../features/middleware.md)
- [示例代码](../../examples/middleware_example.py)
