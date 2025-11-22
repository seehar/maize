# 请求 - Request

## 简介

`Request` 是 maize 对 HTTP 请求的封装，用于适配不同的下载器。

可以在爬虫的 `start_requests`、`parse` 等方法中返回 `Request`，引擎会将请求加入队列并调度执行。

## 创建 Request

### 基本用法

```python
from maize import Request


# 最简单的 GET 请求
request = Request(url="http://www.example.com")

# 指定回调函数
request = Request(
    url="http://www.example.com",
    callback=self.parse_detail
)
```

### 在 Spider 中使用

```python
from typing import Any, AsyncGenerator

from maize import Request, Response, Spider


class MySpider(Spider):
    async def start_requests(self) -> AsyncGenerator[Request, Any]:
        # 生成初始请求
        yield Request(url="http://www.example.com")

    async def parse(self, response: Response):
        # 下发新请求
        yield Request(
            url="http://www.example.com/detail",
            callback=self.parse_detail
        )

    async def parse_detail(self, response: Response):
        print(response.text)
```

## 参数详解

### 基础参数

| 参数名       | 类型         | 是否必须 | 默认值     | 说明                        |
|:----------|:-----------|:-----|:--------|:--------------------------|
| `url`     | `str`      | 是    | -       | 请求的 URL                   |
| `method`  | `Method`   | 否    | `GET`   | 请求方式：GET、POST、PUT、DELETE等 |
| `callback` | `Callable` | 否    | `parse` | 解析函数，默认为 parse            |
| `error_callback` | `Callable` | 否    | `None`  | 错误回调函数                    |
| `priority` | `int`      | 否    | `0`     | 请求优先级，数值越大优先级越高           |

### 请求头和参数

| 参数名           | 类型                   | 是否必须 | 默认值    | 说明                           |
|:--------------|:---------------------|:-----|:-------|:-----------------------------|
| `headers`     | `dict`               | 否    | `None` | 请求头                          |
| `headers_func` | `Callable`          | 否    | `None` | 动态生成请求头的异步函数                 |
| `params`      | `dict`               | 否    | `None` | URL 查询参数                     |
| `data`        | `dict \| str`        | 否    | `None` | 请求体（form 表单）                 |
| `json`        | `dict`               | 否    | `None` | JSON 请求体                     |
| `cookies`     | `dict \| list[dict]` | 否    | `None` | 请求 Cookies                   |

### 代理和认证

| 参数名               | 类型     | 是否必须 | 默认值    | 说明       |
|:------------------|:-------|:-----|:-------|:---------|
| `proxy`           | `str`  | 否    | `None` | 代理地址     |
| `proxy_username`  | `str`  | 否    | `None` | 代理用户名    |
| `proxy_password`  | `str`  | 否    | `None` | 代理密码     |

### 其他参数

| 参数名                | 类型     | 是否必须 | 默认值      | 说明                        |
|:-------------------|:-------|:-----|:---------|:--------------------------|
| `encoding`         | `str`  | 否    | `utf-8`  | 响应编码                      |
| `meta`             | `dict` | 否    | `None`   | 自定义数据，可在响应中获取             |
| `follow_redirects` | `bool` | 否    | `True`   | 是否允许重定向                   |
| `max_redirects`    | `int`  | 否    | `20`     | 最大重定向次数                   |

## 使用示例

### GET 请求

```python
# 基本 GET 请求
yield Request(url="http://www.example.com")

# 带查询参数的 GET 请求
yield Request(
    url="http://www.example.com/search",
    params={"q": "python", "page": 1}
)
# 实际请求: http://www.example.com/search?q=python&page=1
```

### POST 请求

```python
from maize.common.constant.request_constant import Method


# Form 表单提交
yield Request(
    url="http://www.example.com/login",
    method=Method.POST,
    data={
        "username": "admin",
        "password": "123456"
    }
)

# JSON 提交
yield Request(
    url="http://api.example.com/data",
    method=Method.POST,
    json={
        "name": "John",
        "age": 30
    }
)
```

### 自定义请求头

```python
# 静态请求头
yield Request(
    url="http://www.example.com",
    headers={
        "User-Agent": "My Spider 1.0",
        "Accept": "application/json",
        "Authorization": "Bearer token123"
    }
)

# 动态请求头（异步函数）
async def get_headers():
    """动态生成请求头"""
    token = await fetch_token()  # 获取最新的 token
    return {
        "Authorization": f"Bearer {token}"
    }

yield Request(
    url="http://api.example.com/data",
    headers_func=get_headers  # 每次请求时都会调用
)
```

### 使用 Cookies

```python
# 字典形式
yield Request(
    url="http://www.example.com",
    cookies={"session_id": "abc123"}
)

# 列表形式（支持更多属性）
yield Request(
    url="http://www.example.com",
    cookies=[
        {
            "name": "session_id",
            "value": "abc123",
            "domain": ".example.com",
            "path": "/",
            "secure": True
        }
    ]
)
```

### 设置代理

```python
# 基本代理
yield Request(
    url="http://www.example.com",
    proxy="http://proxy.example.com:8080"
)

# 带认证的代理
yield Request(
    url="http://www.example.com",
    proxy="http://proxy.example.com:8080",
    proxy_username="user",
    proxy_password="password"
)
```

### 设置优先级

```python
# 重要请求，优先处理
yield Request(
    url="http://www.example.com/important",
    priority=10  # 数值越大，优先级越高
)

# 普通请求
yield Request(
    url="http://www.example.com/normal",
    priority=1
)
```

### 使用 meta 传递数据

```python
class MySpider(Spider):
    async def parse(self, response: Response):
        """解析列表页"""
        items = response.xpath('//div[@class="item"]')

        for item in items:
            title = item.xpath('.//h3/text()').get()
            price = item.xpath('.//span[@class="price"]/text()').get()
            detail_url = item.xpath('.//a/@href').get()

            # 通过 meta 传递数据到下一个解析函数
            yield Request(
                url=response.urljoin(detail_url),
                callback=self.parse_detail,
                meta={
                    'title': title,
                    'price': price
                }
            )

    async def parse_detail(self, response: Response):
        """解析详情页"""
        # 从 meta 中获取之前传递的数据
        title = response.request.meta.get('title')
        price = response.request.meta.get('price')

        # 提取详情
        description = response.xpath('//div[@class="desc"]/text()').get()

        yield {
            'title': title,
            'price': price,
            'description': description,
            'url': response.url
        }
```

### 设置错误回调

```python
class MySpider(Spider):
    async def start_requests(self):
        yield Request(
            url="http://www.example.com",
            callback=self.parse,
            error_callback=self.handle_error  # 设置错误回调
        )

    async def parse(self, response: Response):
        print(response.text)

    async def handle_error(self, request: Request):
        """处理请求失败"""
        self.logger.error(f"请求失败: {request.url}")

        # 可以选择重新发起请求
        if request.current_retry_count < 3:
            yield Request(
                url=request.url,
                callback=self.parse,
                error_callback=self.handle_error
            )
        else:
            self.logger.error(f"请求多次失败，放弃: {request.url}")
```

### 自定义编码

```python
# 指定响应编码
yield Request(
    url="http://www.example.com",
    encoding="gbk"  # 适用于一些中文网站
)
```

### 控制重定向

```python
# 禁止重定向
yield Request(
    url="http://www.example.com",
    follow_redirects=False
)

# 限制重定向次数
yield Request(
    url="http://www.example.com",
    follow_redirects=True,
    max_redirects=5
)
```

## Request 属性和方法

### 属性

```python
request = Request(url="http://www.example.com", meta={"key": "value"})

# 访问属性
print(request.url)              # URL
print(request.method)           # 请求方法
print(request.priority)         # 优先级
print(request.meta)             # 自定义数据
print(request.current_retry_count)  # 当前重试次数
```

### 方法

```python
# 获取 meta 数据
meta = request.meta

# 增加重试计数
request.retry()

# 获取请求哈希值（用于去重）
hash_value = request.hash
```

## 高级用法

### 批量生成请求

```python
async def start_requests(self):
    """批量生成请求"""
    base_url = "http://www.example.com/page"

    for page in range(1, 101):
        yield Request(
            url=f"{base_url}/{page}",
            callback=self.parse,
            meta={'page': page}
        )
```

### 根据响应动态生成请求

```python
async def parse(self, response: Response):
    """解析页面，提取链接"""
    # 提取所有详情页链接
    links = response.xpath('//a[@class="detail"]/@href').getall()

    for link in links:
        yield Request(
            url=response.urljoin(link),
            callback=self.parse_detail
        )

    # 提取下一页链接
    next_page = response.xpath('//a[@class="next"]/@href').get()
    if next_page:
        yield Request(
            url=response.urljoin(next_page),
            callback=self.parse
        )
```

### 带去重的请求

```python
class MySpider(Spider):
    def __init__(self):
        super().__init__()
        self.visited_urls = set()

    async def parse(self, response: Response):
        links = response.xpath('//a/@href').getall()

        for link in links:
            url = response.urljoin(link)

            # 简单的去重逻辑
            if url not in self.visited_urls:
                self.visited_urls.add(url)
                yield Request(url=url, callback=self.parse_detail)
```

## 注意事项

1. **优先级范围**：priority 可以是任意整数，建议使用 0-100 的范围
2. **Request 与配置**：Request 中的参数（如 proxy）优先级高于全局配置
3. **callback 必须是异步函数**：所有的回调函数都必须是 async 函数
4. **meta 数据传递**：meta 会自动传递到 Response.request.meta 中
5. **重试机制**：框架会自动处理请求失败重试，可通过 max_retry_count 配置

## 下一步

- [Response 详解](response.md) - 响应的处理方法
- [Spider 进阶](spider.md) - 学习更多爬虫特性
- [配置说明](settings.md) - 详细的配置选项
