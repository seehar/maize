# 响应 - Response

## 简介

`Response` 是 maize 对 HTTP 响应的封装，用于适配不同的下载器。在爬虫的 `parse` 方法中，您会接收到 `Response` 对象，可以使用它来解析和处理响应数据。

### 主要功能

- **数据提取**：支持 XPath、CSS 选择器等多种提取方式
- **编码处理**：自动处理各种字符编码
- **JSON 解析**：快速解析 JSON 响应
- **Cookie 管理**：方便地获取和处理 Cookie
- **URL 处理**：自动拼接相对路径为绝对路径
- **元数据传递**：获取从 Request 传递的自定义数据

## 属性说明

### 基础属性

| 属性名               | 类型                 | 说明                       |
|:------------------|:-------------------|:-------------------------|
| `url`             | `str`              | 响应的 URL                  |
| `status`          | `int`              | HTTP 状态码（如 200、404）      |
| `headers`         | `Dict[str, Any]`   | 响应头字典                    |
| `request`         | `Request`          | 对应的请求对象                  |
| `encoding`        | `str`              | 响应编码（默认从 Request 继承）     |
| `driver`          | `Optional[Driver]` | 浏览器驱动（RPA 爬虫时可用）         |
| `source_response` | `Optional[Any]`    | 原始响应对象（如 httpx.Response） |

### 属性使用示例

```python
from maize import Response, Spider


class MySpider(Spider):
    async def parse(self, response: Response):
        # 获取基础信息
        print(f"URL: {response.url}")
        print(f"状态码: {response.status}")
        print(f"编码: {response.encoding}")

        # 获取响应头
        content_type = response.headers.get("Content-Type")
        print(f"内容类型: {content_type}")

        # 获取原始请求
        print(f"请求方法: {response.request.method}")
        print(f"请求URL: {response.request.url}")
```

## 响应内容

### text - 文本内容

返回字符串类型的响应体，会自动处理编码。

**返回值：** `str`

**示例：**
```python
async def parse(self, response: Response):
    # 获取文本内容
    html = response.text
    print(f"响应内容长度: {len(html)}")
    print(f"前100个字符: {html[:100]}")
```

**编码处理：**
```python
# Response 会自动检测编码，按以下优先级：
# 1. Request 中指定的 encoding
# 2. 响应头 Content-Type 中的 charset
# 3. HTML 中的 meta charset
# 4. 默认使用 utf-8

# 如果自动检测失败，可以在 Request 中指定：
yield Request(url="http://example.com", encoding="gbk")
```

### body - 二进制内容

返回字节类型的响应体，适用于下载图片、文件等。

**返回值：** `bytes`

**示例：**
```python
async def parse(self, response: Response):
    # 下载图片
    image_data = response.body

    # 保存到文件
    with open("image.jpg", "wb") as f:
        f.write(image_data)

    # 获取文件大小
    size = len(response.body)
    print(f"文件大小: {size} bytes")
```

## 数据提取方法

### xpath() - XPath 选择器

使用 XPath 表达式提取数据，基于 `parsel` 库实现。

**参数：**
- `xpath` (str): XPath 表达式

**返回值：** `SelectorList[Selector]`

**基础用法：**
```python
async def parse(self, response: Response):
    # 提取单个元素
    title = response.xpath('//title/text()').get()
    print(f"标题: {title}")

    # 提取所有匹配元素
    links = response.xpath('//a/@href').getall()
    print(f"找到 {len(links)} 个链接")

    # 提取带默认值
    author = response.xpath('//meta[@name="author"]/@content').get(default="未知作者")
```

**高级用法：**
```python
async def parse(self, response: Response):
    # 链式调用
    items = response.xpath('//div[@class="item"]')
    for item in items:
        title = item.xpath('.//h3/text()').get()
        price = item.xpath('.//span[@class="price"]/text()').get()
        print(f"{title}: {price}")

    # 使用 XPath 函数
    normalized_text = response.xpath('normalize-space(//p[@class="desc"]/text())').get()

    # 条件选择
    first_item = response.xpath('//div[@class="item"][1]')

    # 包含文本的元素
    links = response.xpath('//a[contains(text(), "下一页")]/@href').get()
```

**常用 XPath 表达式：**
```python
# 选择所有 <a> 标签
response.xpath('//a')

# 选择 class 为 "item" 的 div
response.xpath('//div[@class="item"]')

# 选择 id 为 "content" 的元素
response.xpath('//*[@id="content"]')

# 选择包含特定文本的元素
response.xpath('//div[contains(text(), "关键词")]')

# 选择包含特定 class 的元素（支持多个 class）
response.xpath('//div[contains(@class, "item")]')

# 选择父元素
response.xpath('//span[@class="price"]/parent::div')

# 选择后续兄弟元素
response.xpath('//h3/following-sibling::p')
```

### css() - CSS 选择器

使用 CSS 选择器提取数据（通过 parsel 的 xpath 转换实现）。

**参数：**
- `selector` (str): CSS 选择器

**返回值：** `SelectorList[Selector]`

**基础用法：**
```python
async def parse(self, response: Response):
    # 提取单个元素
    title = response.css('title::text').get()

    # 提取所有链接
    links = response.css('a::attr(href)').getall()

    # 提取 class 为 "item" 的元素
    items = response.css('.item')

    # 提取 id 为 "header" 的元素
    header = response.css('#header')
```

**高级用法：**
```python
async def parse(self, response: Response):
    # 链式调用
    items = response.css('div.item')
    for item in items:
        title = item.css('h3::text').get()
        price = item.css('span.price::text').get()

    # 组合选择器
    links = response.css('div.container > a.link')

    # 伪类选择器
    first_item = response.css('div.item:first-child')
    last_item = response.css('div.item:last-child')

    # 属性选择器
    external_links = response.css('a[target="_blank"]::attr(href)').getall()
```

**XPath vs CSS 对比：**
```python
# 提取文本
response.xpath('//h1/text()').get()
response.css('h1::text').get()

# 提取属性
response.xpath('//a/@href').getall()
response.css('a::attr(href)').getall()

# Class 选择
response.xpath('//div[@class="item"]')
response.css('div.item')

# ID 选择
response.xpath('//*[@id="content"]')
response.css('#content')

# 包含文本（XPath 更强大）
response.xpath('//div[contains(text(), "keyword")]')
# CSS 不直接支持文本匹配
```

### json() - JSON 解析

解析 JSON 格式的响应，基于 `ujson` 实现。

**返回值：** `Dict[str, Any]`

**示例：**
```python
async def parse(self, response: Response):
    # 解析 JSON API 响应
    data = response.json()

    # 访问数据
    status = data.get('status')
    items = data.get('data', [])

    for item in items:
        print(f"ID: {item['id']}, Name: {item['name']}")
```

**错误处理：**
```python
async def parse(self, response: Response):
    try:
        data = response.json()
    except (ValueError, ujson.JSONDecodeError) as e:
        self.logger.error(f"JSON 解析失败: {e}")
        self.logger.debug(f"响应内容: {response.text[:200]}")
        return

    # 处理数据...
```

### urljoin() - URL 拼接

将相对路径转换为绝对路径，基于响应的 URL。

**参数：**
- `url` (str): 相对或绝对 URL

**返回值：** `str` - 绝对 URL

**示例：**
```python
async def parse(self, response: Response):
    # 假设当前 URL: http://example.com/page/1

    # 相对路径
    url1 = response.urljoin('/about')
    # 结果: http://example.com/about

    url2 = response.urljoin('../contact')
    # 结果: http://example.com/contact

    url3 = response.urljoin('detail/123')
    # 结果: http://example.com/page/detail/123

    # 绝对路径（保持不变）
    url4 = response.urljoin('http://other.com/page')
    # 结果: http://other.com/page
```

**实际应用：**
```python
async def parse(self, response: Response):
    # 提取所有链接并转换为绝对路径
    links = response.xpath('//a/@href').getall()

    for link in links:
        absolute_url = response.urljoin(link)
        yield Request(url=absolute_url, callback=self.parse_detail)
```

## Cookie 处理

### cookies - Cookie 字典

返回字典类型的 Cookie，键为 Cookie 名称，值为 Cookie 值。

**返回值：** `Dict[str, Any]`

**示例：**
```python
async def parse(self, response: Response):
    # 获取所有 Cookie
    cookies = response.cookies

    # 访问特定 Cookie
    session_id = cookies.get('sessionid')
    user_id = cookies.get('user_id')

    print(f"Session ID: {session_id}")
    print(f"User ID: {user_id}")
```

### cookie_list - Cookie 列表

返回列表类型的 Cookie，包含完整的 Cookie 信息。适用于需要处理同名 Cookie 的场景。

**返回值：** `List[Dict[str, str]]`

**Cookie 字典结构：**
```python
{
    "name": "sessionid",
    "value": "abc123",
    "domain": ".example.com",
    "path": "/",
    "expires": "Wed, 01 Jan 2025 00:00:00 GMT",
    "secure": True,
    "httponly": True
}
```

**示例：**
```python
async def parse(self, response: Response):
    # 获取完整的 Cookie 列表
    cookie_list = response.cookie_list

    for cookie in cookie_list:
        print(f"Name: {cookie['name']}")
        print(f"Value: {cookie['value']}")
        print(f"Domain: {cookie['domain']}")
        print(f"Path: {cookie['path']}")
        print(f"Secure: {cookie.get('secure', False)}")
        print(f"HttpOnly: {cookie.get('httponly', False)}")
        print("-" * 50)

    # 查找特定 Cookie
    session_cookies = [c for c in cookie_list if c['name'] == 'sessionid']

    # 按域名筛选
    domain_cookies = [c for c in cookie_list if '.example.com' in c['domain']]
```

## 元数据传递

### meta - 获取自定义数据

获取从 Request 中通过 `meta` 参数传递的自定义数据。

**返回值：** `Dict[str, Any]`

**示例：**
```python
class MySpider(Spider):
    async def parse(self, response: Response):
        # 在列表页提取数据并传递到详情页
        items = response.xpath('//div[@class="item"]')

        for item in items:
            title = item.xpath('.//h3/text()').get()
            category = item.xpath('.//span[@class="category"]/text()').get()
            detail_url = item.xpath('.//a/@href').get()

            # 通过 meta 传递数据
            yield Request(
                url=response.urljoin(detail_url),
                callback=self.parse_detail,
                meta={
                    'title': title,
                    'category': category
                }
            )

    async def parse_detail(self, response: Response):
        # 获取传递的数据
        title = response.meta.get('title')
        category = response.meta.get('category')

        # 提取详情页数据
        description = response.xpath('//div[@class="desc"]/text()').get()
        price = response.xpath('//span[@class="price"]/text()').get()

        yield {
            'title': title,
            'category': category,
            'description': description,
            'price': price,
            'url': response.url
        }
```

## 完整使用示例

### 示例1：解析列表页

```python
from typing import Any, AsyncGenerator

from maize import Request, Response, Spider


class ListSpider(Spider):
    async def start_requests(self) -> AsyncGenerator[Request, Any]:
        yield Request(url="http://example.com/products")

    async def parse(self, response: Response):
        # 检查状态码
        if response.status != 200:
            self.logger.error(f"请求失败: {response.status}")
            return

        # 提取商品列表
        products = response.xpath('//div[@class="product"]')

        for product in products:
            # 提取基本信息
            title = product.xpath('.//h3/text()').get()
            price = product.xpath('.//span[@class="price"]/text()').get()
            image = product.xpath('.//img/@src').get()
            link = product.xpath('.//a/@href').get()

            # 提交数据
            yield {
                'title': title,
                'price': price,
                'image': response.urljoin(image) if image else None,
                'url': response.urljoin(link) if link else None
            }

        # 翻页
        next_page = response.xpath('//a[@class="next"]/@href').get()
        if next_page:
            yield Request(
                url=response.urljoin(next_page),
                callback=self.parse
            )
```

### 示例2：解析 JSON API

```python
class ApiSpider(Spider):
    async def start_requests(self):
        yield Request(url="http://api.example.com/data?page=1")

    async def parse(self, response: Response):
        # 解析 JSON
        data = response.json()

        # 提取数据
        items = data.get('items', [])
        for item in items:
            yield {
                'id': item['id'],
                'name': item['name'],
                'value': item['value']
            }

        # 翻页
        current_page = data.get('page', 1)
        total_pages = data.get('total_pages', 1)

        if current_page < total_pages:
            next_page = current_page + 1
            yield Request(
                url=f"http://api.example.com/data?page={next_page}",
                callback=self.parse
            )
```

### 示例3：处理 Cookie

```python
class LoginSpider(Spider):
    async def start_requests(self):
        # 登录
        yield Request(
            url="http://example.com/login",
            method=Method.POST,
            data={'username': 'user', 'password': 'pass'},
            callback=self.after_login
        )

    async def after_login(self, response: Response):
        # 检查登录是否成功
        cookies = response.cookies
        session_id = cookies.get('sessionid')

        if not session_id:
            self.logger.error("登录失败")
            return

        self.logger.info(f"登录成功，Session ID: {session_id}")

        # 使用 Cookie 访问需要登录的页面
        yield Request(
            url="http://example.com/profile",
            cookies=cookies,
            callback=self.parse_profile
        )
```

## 最佳实践

### 1. 检查响应状态

```python
async def parse(self, response: Response):
    # 检查状态码
    if response.status != 200:
        self.logger.warning(f"异常状态码: {response.status}")
        return

    # 检查内容类型
    content_type = response.headers.get('Content-Type', '')
    if 'text/html' not in content_type:
        self.logger.warning(f"非HTML响应: {content_type}")
        return

    # 处理数据...
```

### 2. 安全地提取数据

```python
async def parse(self, response: Response):
    # 使用 get() 提供默认值
    title = response.xpath('//title/text()').get(default='无标题')

    # 检查是否为空
    description = response.xpath('//meta[@name="description"]/@content').get()
    if not description:
        self.logger.warning("未找到描述信息")

    # 处理可能为 None 的值
    price = response.xpath('//span[@class="price"]/text()').get()
    if price:
        # 清理和转换
        price = price.strip().replace('¥', '').replace(',', '')
        try:
            price = float(price)
        except ValueError:
            self.logger.warning(f"价格格式错误: {price}")
            price = 0.0
```

### 3. 使用正则表达式

```python
import re

async def parse(self, response: Response):
    # 在 XPath 中使用正则
    phones = response.xpath('//text()[re:test(., "\d{11}")]').getall()

    # 在 Python 中使用正则
    text = response.text
    emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
```

### 4. 处理编码问题

```python
# 在 Request 中指定编码
yield Request(url="http://example.com", encoding="gbk")

# 或在 parse 中处理
async def parse(self, response: Response):
    try:
        text = response.text
    except UnicodeDecodeError:
        # 尝试其他编码
        text = response.body.decode('gbk', errors='ignore')
```

## 注意事项

1. **延迟解析**：XPath 和 CSS 选择器的解析是延迟的，只在首次调用时执行
2. **内存缓存**：`text`、`body`、`cookies` 等属性会被缓存，多次访问不会重复计算
3. **编码处理**：框架会自动检测编码，但复杂情况下可能需要手动指定
4. **空值处理**：使用 `.get()` 而不是 `.getall()[0]` 来避免索引错误
5. **链式调用**：XPath 和 CSS 支持链式调用，可以先定位再提取

## 下一步

- [Request 详解](request.md) - 了解如何构造请求
- [Spider 进阶](spider.md) - 学习更多爬虫技巧
- [Item 详解](item.md) - 了解数据结构定义
