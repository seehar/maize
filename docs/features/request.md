# 请求 - Request

## 简介

`Request` 为 `maize` 为了适配不同下载器对请求进行的封装。
可以在爬虫的 `start_requests`, `parse` 返回 `Request`，
引擎会将请求入队，进行请求下载。

## 参数详解

> 请注意，`Request` 中参数的优先级高于项目配置文件中的参数。比如：`proxy`

| 参数名              | 类型         | 是否必须  | 默认值     | 说明                                         |
|:-----------------|:-----------|:------|:--------|:-------------------------------------------|
| `url`            | `str`      | 是     |         | 请求的 `url`                                  |
| `method`         | `str`      | 否     | `GET`   | 请求方式，如 `GET`, `POST`, `PUT`                |
| `callback`       | `Callable` | 否     | `parse` | 自定义的解析函数，默认为 `parse`                       |
| `priority`       | `int`      | 否     | `None`  | 请求优先级，默认为 `0`                              |
| `headers`        | `dict`     | 否     | `None`  | 请求头                                        |
| `params`         | `dict`     | 否     | `None`  | 请求参数                                       |
| `data`           | `dict`     | `str` | 否       | `None`                                     | 请求 `body`                                  |
| `json`           | `dict`     | 否     | `None`  | `dict` 类型的 `body`                          |
| `cookies`        | `dict`     | 否     | `None`  | 请求 `cookies`                               |
| `proxy`          | `str`      | 否     | `None`  | 代理 `ip`                                    |
| `proxy_username` | `str`      | 否     | `None`  | 代理 `ip` 用户名                                |
| `proxy_password` | `str`      | 否     | `None`  | 代理 `ip` 密码                                 |
| `encoding`       | `str`      | 否     | `utf-8` | 编码，当无法解析时，使用响应中的编码尝试，如还无法解析，会抛出异常          |
| `meta`           | `dict`     | 否     | `None`  | 自定义数据，会传递到 `Response` 中，可在 `Response` 中获取到 |

## 方法详解

设置和获取自定义数据，可以在下载后的 `Response` 中获取到

```python
from maize import Request

# 设置 meta
request = Request("url", meta={"a": 1})

# 获取 meta
meta = request.meta
```
