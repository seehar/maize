# Downloader 下载器

## 简介

Downloader（下载器）是 maize 框架中负责执行 HTTP 请求的核心组件。框架采用插拔式设计，支持多种下载器，您可以根据需求选择或自定义。

### 主要功能

- **HTTP 请求执行**：发送 GET、POST 等各种 HTTP 请求
- **并发控制**：支持高并发异步请求
- **会话管理**：自动管理 Cookie 和连接池
- **代理支持**：支持 HTTP/HTTPS 代理
- **重试机制**：自动处理请求失败重试
- **响应处理**：将原始响应转换为 maize Response 对象

## 内置下载器

maize 内置了 4 种下载器，满足不同的使用场景。

### 下载器列表

| 下载器                       | 基础库        | 特点                | 适用场景              |
|:--------------------------|:-----------|:------------------|:------------------|
| `AioHttpDownloader`       | aiohttp    | 默认下载器，性能优秀，稳定性好 | 一般网页采集，推荐首选      |
| `HTTPXDownloader`         | httpx      | 支持 HTTP/2        | 需要 HTTP/2 支持的场景  |
| `PlaywrightDownloader`    | playwright | 浏览器自动化，支持 JS 渲染  | 动态渲染页面，复杂交互      |
| `PatchrightDownloader`    | patchright | 反检测能力更强的浏览器自动化  | 反爬虫较强的网站         |

### 1. AioHttpDownloader（默认）

基于 aiohttp 实现，性能优秀，是框架的默认下载器。

**特点：**
- ✅ 高性能异步 HTTP 客户端
- ✅ 连接池管理
- ✅ 会话保持
- ✅ 良好的稳定性

**使用方式：**
```python
from maize import SpiderSettings

settings = SpiderSettings(
    downloader="maize.AioHttpDownloader"  # 默认值，可省略
)
```

### 2. HTTPXDownloader

基于 httpx 实现，支持 HTTP/2 协议。

**特点：**
- ✅ 支持 HTTP/2
- ✅ 现代化的 API 设计
- ✅ 与 requests 库类似的接口
- ⚠️ 不支持会话保持（`use_session` 配置无效）

**使用方式：**
```python
from maize import SpiderSettings

settings = SpiderSettings(
    downloader="maize.HTTPXDownloader"
)
```

### 3. PlaywrightDownloader

基于 Playwright 实现的浏览器自动化下载器。

**特点：**
- ✅ 支持 JavaScript 渲染
- ✅ 可以执行复杂的页面交互
- ✅ 支持多种浏览器（Chromium、Firefox、WebKit）
- ✅ 截图、PDF 生成等功能
- ⚠️ 性能相对较低，资源占用大

**安装：**
```bash
pip install maize[rpa]
playwright install
```

**使用方式：**
```python
from maize import SpiderSettings

settings = SpiderSettings(
    downloader="maize.downloader.playwright_downloader.PlaywrightDownloader"
)

# 配置浏览器参数
settings.rpa.headless = False  # 显示浏览器窗口
settings.rpa.driver_type = "chromium"  # 浏览器类型
settings.rpa.window_size = (1920, 1080)
settings.rpa.skip_resource_types = ["image", "media", "font"]  # 不加载图片等资源
```

### 4. PatchrightDownloader

基于 Patchright 实现，是 Playwright 的增强版本，具有更强的反检测能力。

**特点：**
- ✅ 所有 Playwright 的功能
- ✅ 更强的反爬虫检测能力
- ✅ 绕过大部分浏览器指纹识别
- ⚠️ 性能和资源占用与 Playwright 相同

**安装：**
```bash
pip install maize[rpa]
```

**使用方式：**
```python
from maize import SpiderSettings

settings = SpiderSettings(
    downloader="maize.downloader.patchright_downloader.PatchrightDownloader"
)
```

## 配置下载器

### 方式一：使用 SpiderSettings

```python
from maize import Spider, SpiderSettings


if __name__ == "__main__":
    settings = SpiderSettings(
        project_name="我的爬虫",
        downloader="maize.HTTPXDownloader"  # 指定下载器
    )

    MySpider().run(settings=settings)
```

### 方式二：在配置文件中指定

```python
# settings.py
from maize import SpiderSettings


class Settings(SpiderSettings):
    downloader = "maize.HTTPXDownloader"
```

### 方式三：使用 custom_settings

```python
from maize import Spider


class MySpider(Spider):
    custom_settings = {
        "downloader": "maize.HTTPXDownloader"
    }

    # ...爬虫实现...
```

## 自定义下载器

如果内置下载器不能满足需求，可以自定义下载器。

### 基本结构

继承 `BaseDownloader` 并实现必要的方法：

```python
import typing

from maize import BaseDownloader, Request, Response

if typing.TYPE_CHECKING:
    from maize.core.crawler import Crawler


class CustomDownloader(BaseDownloader):
    """自定义下载器"""

    def __init__(self, crawler: "Crawler"):
        super().__init__(crawler)
        # 初始化自定义属性
        self.client = None

    async def open(self):
        """
        下载器初始化时调用
        可以在这里创建 HTTP 客户端、连接池等资源
        """
        await super().open()

        # 获取配置
        timeout = self.crawler.settings.request.request_timeout
        verify_ssl = self.crawler.settings.request.verify_ssl

        # 初始化 HTTP 客户端
        # self.client = YourHttpClient(timeout=timeout, verify_ssl=verify_ssl)

        self.logger.info("自定义下载器已初始化")

    async def close(self):
        """
        下载器关闭时调用
        必须在这里释放所有资源
        """
        await super().close()

        # 关闭客户端
        if self.client:
            await self.client.close()

        self.logger.info("自定义下载器已关闭")

    async def download(self, request: Request) -> typing.Optional[Response]:
        """
        执行下载（必须实现）

        :param request: 请求对象
        :return: 响应对象，如果失败返回 None
        """
        # 随机等待（如果配置了 random_wait_time）
        await self.random_wait()

        try:
            # 记录日志
            self.logger.debug(f"正在下载: {request.url}")

            # 执行请求
            # response = await self.client.get(request.url, headers=request.headers)

            # 构造响应对象
            # return self.structure_response(request, response, response.content)

            pass  # 实际实现时删除这行

        except Exception as e:
            # 处理重试
            if new_request := await self._download_retry(request, e):
                return new_request

            self.logger.error(f"请求失败: {e}")
            return None

    @staticmethod
    def structure_response(
        request: Request,
        response: typing.Any,
        body: bytes
    ) -> Response:
        """
        构造 maize Response 对象（必须实现）

        :param request: 请求对象
        :param response: 原始响应对象
        :param body: 响应体（字节）
        :return: maize Response 对象
        """
        return Response(
            url=str(response.url),
            headers=dict(response.headers),
            status=response.status_code,
            body=body,
            request=request,
        )

    async def process_error_request(self, request: Request):
        """
        处理超过最大重试次数的请求（可选）

        :param request: 失败的请求
        """
        self.logger.error(f"请求最终失败: {request.url}")
        # 可以将失败的请求保存到文件或数据库
```

### 使用自定义下载器

```python
from maize import SpiderSettings

settings = SpiderSettings(
    downloader="your_module.CustomDownloader"  # 指定自定义下载器的完整路径
)
```

## 完整示例：基于 requests 的下载器

虽然不推荐在异步框架中使用同步库，但这里提供一个教学示例：

```python
import typing
from concurrent.futures import ThreadPoolExecutor

import requests

from maize import BaseDownloader, Request, Response

if typing.TYPE_CHECKING:
    from maize.core.crawler import Crawler


class RequestsDownloader(BaseDownloader):
    """基于 requests 库的下载器（仅作示例，不推荐生产使用）"""

    def __init__(self, crawler: "Crawler"):
        super().__init__(crawler)
        self.session = None
        self.executor = None

    async def open(self):
        await super().open()

        # 创建 requests Session
        self.session = requests.Session()

        # 设置超时
        timeout = self.crawler.settings.request.request_timeout
        self.session.timeout = timeout

        # 创建线程池（用于在异步中执行同步请求）
        self.executor = ThreadPoolExecutor(max_workers=10)

        self.logger.info("RequestsDownloader 已初始化")

    async def close(self):
        await super().close()

        if self.session:
            self.session.close()

        if self.executor:
            self.executor.shutdown(wait=True)

        self.logger.info("RequestsDownloader 已关闭")

    async def download(self, request: Request) -> typing.Optional[Response]:
        await self.random_wait()

        try:
            # 在线程池中执行同步请求
            import asyncio
            loop = asyncio.get_event_loop()

            response = await loop.run_in_executor(
                self.executor,
                self._sync_request,
                request
            )

            return self.structure_response(request, response, response.content)

        except Exception as e:
            if new_request := await self._download_retry(request, e):
                return new_request

            self.logger.error(f"请求失败: {e}")
            return None

    def _sync_request(self, request: Request) -> requests.Response:
        """同步执行请求"""
        return self.session.request(
            method=request.method,
            url=request.url,
            headers=request.headers,
            params=request.params,
            data=request.data,
            json=request.json,
            cookies=request.cookies,
            timeout=self.session.timeout,
        )

    @staticmethod
    def structure_response(
        request: Request,
        response: requests.Response,
        body: bytes
    ) -> Response:
        return Response(
            url=response.url,
            headers=dict(response.headers),
            status=response.status_code,
            body=body,
            request=request,
        )
```

## 下载器对比

### 性能对比

| 下载器                    | 并发性能  | 内存占用 | 适合并发数 |
|:-----------------------|:------|:-----|:------|
| `AioHttpDownloader`    | ⭐⭐⭐⭐⭐ | 低    | 100+  |
| `HTTPXDownloader`      | ⭐⭐⭐⭐  | 低    | 50+   |
| `PlaywrightDownloader` | ⭐⭐    | 高    | 5-10  |
| `PatchrightDownloader` | ⭐⭐    | 高    | 5-10  |

### 功能对比

| 功能       | AioHttp | HTTPX | Playwright | Patchright |
|:---------|:--------|:------|:-----------|:-----------|
| HTTP/1.1 | ✅       | ✅     | ✅          | ✅          |
| HTTP/2   | ❌       | ✅     | ✅          | ✅          |
| 会话保持     | ✅       | ❌     | ✅          | ✅          |
| JS 渲染    | ❌       | ❌     | ✅          | ✅          |
| 页面交互     | ❌       | ❌     | ✅          | ✅          |
| 反检测      | ❌       | ❌     | ⭐          | ⭐⭐⭐        |
| 截图功能     | ❌       | ❌     | ✅          | ✅          |

## 下载器选择建议

### 1. 一般网页采集
**推荐：** `AioHttpDownloader`

适用于大部分静态或简单动态网页。

```python
settings = SpiderSettings(
    concurrency=50,  # 可以设置较高的并发
    downloader="maize.AioHttpDownloader"
)
```

### 2. 需要 HTTP/2
**推荐：** `HTTPXDownloader`

某些网站只支持或优先使用 HTTP/2。

```python
settings = SpiderSettings(
    concurrency=30,
    downloader="maize.HTTPXDownloader"
)
```

### 3. 动态渲染页面
**推荐：** `PlaywrightDownloader`

页面内容由 JavaScript 动态生成，或需要等待 AJAX 请求。

```python
settings = SpiderSettings(
    concurrency=5,  # 浏览器并发不宜过高
    downloader="maize.downloader.playwright_downloader.PlaywrightDownloader"
)
settings.rpa.headless = True
settings.rpa.wait_until = "networkidle"
```

### 4. 反爬虫强的网站
**推荐：** `PatchrightDownloader`

网站有严格的浏览器指纹检测。

```python
settings = SpiderSettings(
    concurrency=3,  # 降低并发避免被封
    downloader="maize.downloader.patchright_downloader.PatchrightDownloader"
)
settings.rpa.use_stealth_js = True
```

## 最佳实践

### 1. 合理设置并发数

不同下载器的并发能力不同：

```python
# HTTP 下载器
settings = SpiderSettings(concurrency=50)  # AioHttp/HTTPX

# 浏览器下载器
settings = SpiderSettings(concurrency=5)   # Playwright/Patchright
```

### 2. 使用会话保持

对于需要登录的网站，使用支持会话的下载器：

```python
settings = SpiderSettings(
    downloader="maize.AioHttpDownloader"
)
settings.request.use_session = True  # 启用会话
```

### 3. 配置代理

```python
settings = SpiderSettings()
settings.proxy.enabled = True
settings.proxy.proxy_url = "proxy.example.com:8080"
settings.proxy.proxy_username = "user"
settings.proxy.proxy_password = "pass"
```

### 4. 优化 RPA 性能

使用浏览器下载器时，跳过不必要的资源：

```python
settings.rpa.skip_resource_types = ["image", "media", "font", "stylesheet"]
settings.rpa.wait_until = "domcontentloaded"  # 不等待所有资源加载
```

### 5. 错误处理

在自定义下载器中正确处理错误：

```python
async def download(self, request: Request):
    try:
        # 下载逻辑
        pass
    except TimeoutError as e:
        # 超时错误
        if new_request := await self._download_retry(request, e):
            return new_request
    except ConnectionError as e:
        # 连接错误
        if new_request := await self._download_retry(request, e):
            return new_request
    except Exception as e:
        # 其他错误
        self.logger.error(f"未知错误: {e}")
        return None
```

## 常见问题

### 1. 如何在下载器中访问配置？

```python
# 在下载器的 open() 方法中
timeout = self.crawler.settings.request.request_timeout
verify_ssl = self.crawler.settings.request.verify_ssl
concurrency = self.crawler.settings.concurrency
```

### 2. 如何在下载器中记录日志？

```python
self.logger.debug("调试信息")
self.logger.info("普通信息")
self.logger.warning("警告信息")
self.logger.error("错误信息")
```

### 3. 如何实现下载器的资源池？

参考 `AioHttpDownloader` 的实现，使用连接池：

```python
async def open(self):
    await super().open()
    self.connector = TCPConnector(limit=100)  # 连接池大小
    self.session = ClientSession(connector=self.connector)
```

### 4. HTTPXDownloader 为什么不支持会话？

httpx 的设计理念与 aiohttp 不同，每次请求都是独立的。如需会话功能，请使用 `AioHttpDownloader`。

## 注意事项

1. **必须使用异步**：所有方法都必须是异步的（`async def`）
2. **资源释放**：必须在 `close()` 中释放所有资源
3. **错误处理**：使用 `_download_retry()` 处理重试
4. **日志记录**：使用 `self.logger` 记录日志
5. **配置访问**：通过 `self.crawler.settings` 访问配置

## 下一步

- [Request 详解](request.md) - 了解请求对象的详细用法
- [Response 详解](response.md) - 了解响应对象的详细用法
- [配置说明](settings.md) - 查看所有配置选项
