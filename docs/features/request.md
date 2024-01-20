# 请求 - Request

## 简介

`Request` 为 `maize` 为了适配不同下载器对请求进行的封装。
可以在爬虫的 `start_requests`, `parse` 返回 `Request`，
引擎会将请求入队，进行请求下载。

## 参数详解

```text
@param url: 待抓取的url
@param method: 请求方式，如 GET, POST, PUT，默认 GET
@param callback: 自定义的解析函数，默认为 parse
@param priority: 请求优先级，默认为 0
@param headers: 请求头
@param params: 请求参数
@param data: 请求 body
@param cookies: 字典
@param proxies: 代理ip
@param encoding: 编码，默认utf-8，当无法解析时，使用响应中的编码
@param meta: 自定义数据
```

## 方法详解

设置和获取自定义数据，可以在下载后的 `Response` 中获取到

```python
from maize import Request

# 设置 meta
request = Request("url", meta={"a": 1})

# 获取 meta
meta = request.meta
```
