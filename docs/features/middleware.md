# 中间件系统 (Middleware System)

Maize 框架提供了一个强大而灵活的中间件系统，允许你在请求/响应处理的各个阶段插入自定义逻辑。

## 概述

中间件系统包含三种类型的中间件：

1. **下载器中间件 (Downloader Middleware)** - 处理请求和响应
2. **爬虫中间件 (Spider Middleware)** - 处理爬虫的输入输出
3. **管道中间件 (Pipeline Middleware)** - 处理 Item 数据

## 中间件类型

### 1. 下载器中间件 (DownloaderMiddleware)

下载器中间件在请求发送到下载器之前和响应返回之后进行处理。

#### 钩子方法

```python
from maize.middlewares import DownloaderMiddleware

class MyDownloaderMiddleware(DownloaderMiddleware):
    async def process_request(self, request, spider):
        """
        在请求发送前处理请求

        返回值:
            - Request: 修改后的请求，继续处理
            - Response: 跳过下载，直接使用该响应
            - None: 丢弃请求，不再处理
        """
        return request

    async def process_response(self, request, response, spider):
        """
        在响应返回后处理响应

        返回值:
            - Response: 修改后的响应，继续处理
            - Request: 重新发送请求（重试）
            - None: 丢弃响应，不再处理
        """
        return response

    async def process_exception(self, request, exception, spider):
        """
        处理下载过程中的异常

        返回值:
            - Request: 重新发送请求
            - Response: 使用该响应替代
            - None: 忽略异常，继续
        """
        return None
```

#### 执行顺序

- `process_request`: 按优先级**升序**执行（数字越小越先执行）
- `process_response`: 按优先级**降序**执行（数字越大越先执行）
- `process_exception`: 按优先级**降序**执行

### 2. 爬虫中间件 (SpiderMiddleware)

爬虫中间件处理进入和离开爬虫的数据流。

#### 钩子方法

```python
from maize.middlewares import SpiderMiddleware

class MySpiderMiddleware(SpiderMiddleware):
    async def process_spider_input(self, response, spider):
        """
        在响应传递给爬虫回调之前处理

        抛出异常会触发 process_spider_exception
        """
        pass

    async def process_spider_output(self, response, result, spider):
        """
        处理爬虫回调返回的结果

        Args:
            result: AsyncGenerator[Request | Item]

        Yields:
            Request 或 Item 对象
        """
        async for item in result:
            yield item

    async def process_spider_exception(self, response, exception, spider):
        """
        处理爬虫回调中的异常

        返回值:
            - AsyncGenerator: 返回新的结果
            - None: 继续传播异常
        """
        return None

    async def process_start_requests(self, start_requests, spider):
        """
        处理 start_requests 生成器

        Yields:
            Request 对象
        """
        async for request in start_requests:
            yield request
```

#### 执行顺序

- `process_start_requests`: 按优先级**降序**执行
- `process_spider_input`: 按优先级**升序**执行
- `process_spider_output`: 按优先级**降序**执行
- `process_spider_exception`: 按优先级**降序**执行

### 3. 管道中间件 (PipelineMiddleware)

管道中间件在 Item 进入和离开 Pipeline 时进行处理。

#### 钩子方法

```python
from maize.middlewares import PipelineMiddleware

class MyPipelineMiddleware(PipelineMiddleware):
    async def process_item_before(self, item, spider):
        """
        在 Item 进入 Pipeline 前处理

        返回值:
            - Item: 修改后的 Item，继续处理
            - None: 丢弃 Item，不再处理
        """
        return item

    async def process_item_after(self, item, spider):
        """
        在 Item 离开 Pipeline 后处理

        返回值:
            - Item: 修改后的 Item
            - None: 丢弃 Item
        """
        return item
```

#### 执行顺序

- `process_item_before`: 按优先级**升序**执行
- `process_item_after`: 按优先级**降序**执行

## 配置中间件

### 方法 1: 在 Spider 中配置

```python
from maize import Spider

class MySpider(Spider):
    custom_settings = {
        'middleware': {
            'downloader_middlewares': {
                'myproject.middlewares.CustomMiddleware': 100,
                'maize.middlewares.downloader.RetryMiddleware': 200,
            },
            'spider_middlewares': {
                'myproject.middlewares.DepthMiddleware': 100,
            },
            'pipeline_middlewares': {
                'myproject.middlewares.ValidationMiddleware': 100,
            },
        }
    }
```

### 方法 2: 在配置文件中配置

#### YAML 配置 (settings.yaml)

```yaml
middleware:
  downloader_middlewares:
    myproject.middlewares.CustomMiddleware: 100
    maize.middlewares.downloader.RetryMiddleware: 200

  spider_middlewares:
    myproject.middlewares.DepthMiddleware: 100

  pipeline_middlewares:
    myproject.middlewares.ValidationMiddleware: 100
```

#### TOML 配置 (settings.toml)

```toml
[middleware.downloader_middlewares]
"myproject.middlewares.CustomMiddleware" = 100
"maize.middlewares.downloader.RetryMiddleware" = 200

[middleware.spider_middlewares]
"myproject.middlewares.DepthMiddleware" = 100

[middleware.pipeline_middlewares]
"myproject.middlewares.ValidationMiddleware" = 100
```

## 内置中间件

### 下载器中间件

#### 1. UserAgentMiddleware

轮换 User-Agent 请求头。

```python
custom_settings = {
    'middleware': {
        'downloader_middlewares': {
            'maize.middlewares.downloader.UserAgentMiddleware': 100,
        }
    },
    'user_agent_list': [
        'Mozilla/5.0 ...',
        'Mozilla/5.0 ...',
    ],
    'user_agent_mode': 'random',  # 或 'sequential'
}
```

#### 2. DefaultHeadersMiddleware

添加默认请求头。

```python
custom_settings = {
    'middleware': {
        'downloader_middlewares': {
            'maize.middlewares.downloader.DefaultHeadersMiddleware': 50,
        }
    },
    'default_headers': {
        'Accept': 'text/html,application/xhtml+xml',
        'Accept-Language': 'en-US,en;q=0.9',
    },
}
```

#### 3. RetryMiddleware

请求重试中间件。

```python
custom_settings = {
    'middleware': {
        'downloader_middlewares': {
            'maize.middlewares.downloader.RetryMiddleware': 200,
        }
    },
    'request': {
        'max_retry_count': 3,
    },
    'retry_http_codes': [500, 502, 503, 504, 408, 429],
    'retry_delay': 1,
    'exponential_backoff': True,
}
```

### 爬虫中间件

#### 1. DepthMiddleware

限制爬取深度。

```python
custom_settings = {
    'middleware': {
        'spider_middlewares': {
            'maize.middlewares.spider.DepthMiddleware': 100,
        }
    },
    'max_depth': 3,
    'depth_priority_enabled': False,
}
```

#### 2. HttpErrorMiddleware

过滤 HTTP 错误响应。

```python
custom_settings = {
    'middleware': {
        'spider_middlewares': {
            'maize.middlewares.spider.HttpErrorMiddleware': 50,
        }
    },
    'http_error_allowed_codes': [200, 201, 202],
    'http_error_log_level': 'warning',
}
```

### 管道中间件

#### 1. ItemValidationMiddleware

验证 Item 数据。

```python
custom_settings = {
    'middleware': {
        'pipeline_middlewares': {
            'maize.middlewares.pipeline.ItemValidationMiddleware': 100,
        }
    },
    'required_fields': ['title', 'url', 'content'],
    'drop_invalid_items': True,
}
```

#### 2. ItemCleanerMiddleware

清理 Item 数据。

```python
custom_settings = {
    'middleware': {
        'pipeline_middlewares': {
            'maize.middlewares.pipeline.ItemCleanerMiddleware': 50,
        }
    },
    'strip_whitespace': True,
    'remove_html': False,
    'normalize_whitespace': True,
    'empty_to_none': False,
    'excluded_fields': ['raw_html'],
}
```

## 创建自定义中间件

### 示例：自定义代理中间件

```python
from maize.middlewares import DownloaderMiddleware
import random

class ProxyMiddleware(DownloaderMiddleware):
    """自定义代理中间件"""

    def __init__(self, settings=None, proxy_list=None):
        super().__init__(settings)
        self.proxy_list = proxy_list or []

    @classmethod
    def from_crawler(cls, crawler):
        """从 crawler 创建中间件实例"""
        proxy_list = getattr(crawler.settings, 'proxy_list', [])
        return cls(crawler.settings, proxy_list=proxy_list)

    async def open(self):
        """中间件启动时调用"""
        self.logger.info(f"Loaded {len(self.proxy_list)} proxies")

    async def process_request(self, request, spider):
        """为请求设置代理"""
        if self.proxy_list:
            proxy = random.choice(self.proxy_list)
            request.proxy = proxy
            self.logger.debug(f"Using proxy: {proxy}")
        return request

    async def process_exception(self, request, exception, spider):
        """处理代理错误"""
        self.logger.warning(f"Proxy error for {request.url}: {exception}")
        # 重试请求
        return request

    async def close(self):
        """中间件关闭时调用"""
        self.logger.info("Proxy middleware closed")
```

### 使用自定义中间件

```python
class MySpider(Spider):
    custom_settings = {
        'middleware': {
            'downloader_middlewares': {
                'myproject.middlewares.ProxyMiddleware': 100,
            }
        },
        'proxy_list': [
            'http://proxy1.com:8080',
            'http://proxy2.com:8080',
        ],
    }
```

## 中间件优先级

优先级是一个整数，决定中间件的执行顺序。建议的优先级范围：

- **0-99**: 系统保留（核心中间件）
- **100-299**: 内置中间件
- **300-599**: 第三方中间件
- **600-999**: 用户自定义中间件

## 最佳实践

### 1. 使用 from_crawler 初始化

```python
@classmethod
def from_crawler(cls, crawler):
    """推荐：使用 from_crawler 访问设置和 crawler"""
    setting_value = getattr(crawler.settings, 'my_setting', default_value)
    return cls(crawler.settings, my_param=setting_value)
```

### 2. 正确处理返回值

```python
async def process_request(self, request, spider):
    # 返回 Request 继续处理
    return request

    # 返回 Response 跳过下载
    # return Response(...)

    # 返回 None 丢弃请求
    # return None
```

### 3. 使用 logger

```python
async def process_request(self, request, spider):
    self.logger.debug(f"Processing request: {request.url}")
    self.logger.info(f"Added header to request")
    self.logger.warning(f"Potential issue detected")
    self.logger.error(f"Error processing request")
    return request
```

### 4. 实现生命周期方法

```python
async def open(self):
    """在爬虫启动时初始化资源"""
    self.db = await connect_to_database()

async def close(self):
    """在爬虫关闭时清理资源"""
    await self.db.close()
```

### 5. 处理异常

```python
async def process_request(self, request, spider):
    try:
        # 处理逻辑
        return request
    except Exception as e:
        self.logger.error(f"Error in middleware: {e}")
        # 决定是否继续处理
        return request  # 或 return None
```

## 常见场景

### 场景 1: 添加自定义请求头

```python
class CustomHeaderMiddleware(DownloaderMiddleware):
    async def process_request(self, request, spider):
        request.headers = request.headers or {}
        request.headers['X-Custom-Header'] = 'value'
        return request
```

### 场景 2: 基于响应状态码重试

```python
class StatusRetryMiddleware(DownloaderMiddleware):
    async def process_response(self, request, response, spider):
        if response.status == 429:  # Too Many Requests
            self.logger.warning("Rate limited, retrying...")
            await asyncio.sleep(5)
            return request  # 重试
        return response
```

### 场景 3: 过滤特定 URL

```python
class UrlFilterMiddleware(SpiderMiddleware):
    async def process_spider_output(self, response, result, spider):
        async for item in result:
            if isinstance(item, Request):
                if 'example.com' not in item.url:
                    continue  # 跳过不匹配的 URL
            yield item
```

### 场景 4: 数据清洗

```python
class DataCleanerMiddleware(PipelineMiddleware):
    async def process_item_before(self, item, spider):
        # 清理数据
        if hasattr(item, 'title'):
            item.title = item.title.strip()
        return item
```

## 调试技巧

### 1. 启用详细日志

```python
custom_settings = {
    'log_level': 'DEBUG',
}
```

### 2. 添加调试信息

```python
async def process_request(self, request, spider):
    self.logger.debug(f"Request URL: {request.url}")
    self.logger.debug(f"Request headers: {request.headers}")
    self.logger.debug(f"Request meta: {request.meta}")
    return request
```

### 3. 统计信息

```python
class StatsMiddleware(DownloaderMiddleware):
    def __init__(self, settings=None):
        super().__init__(settings)
        self.request_count = 0
        self.response_count = 0

    async def process_request(self, request, spider):
        self.request_count += 1
        return request

    async def process_response(self, request, response, spider):
        self.response_count += 1
        return response

    async def close(self):
        self.logger.info(f"Total requests: {self.request_count}")
        self.logger.info(f"Total responses: {self.response_count}")
```

## 参考资料

- [API 文档](../api/middlewares.md)
- [示例代码](../../examples/middleware_example.py)
- [源代码](../../maize/middlewares/)
