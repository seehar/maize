# 响应 - Response

## 简介

`Response` 为 `maize` 为适配不同下载器对响应进行的封装。
爬虫 `parse` 方法中，会返回 `Response` 类型的参数，您可以对响应进行对应对解析和处理

## 参数详解

| 参数名       | 类型        | 是否必须 | 默认值   | 说明            |
|:----------|:----------|:-----|:------|:--------------|
| `url`     | `str`     | 是    |       | 请求的 `url`     |
| `headers` | `dict`    | 是    |       | 响应头           |
| `request` | `Request` | 是    |       | 请求 `Request`  |
| `body`    | `bytes`   | 否    | `b""` | 响应体           |
| `status`  | `int`     | 否    | `200` | 响应状态码，如 `200` |

## 方法详解

### `text`

返回字符串类型的响应体

### `json`

基于 `ujson` 返回格式化的 `json` 类型的数据

### `urljoin`

基于 `urllib` 的 `urljoin` 方法拼接 `url`。
返回一个绝对路径的 `url`，无需您判断传入的时相对路径还是绝对路径

### `xpath`

基于 `parsel` 的 `Selector` 对响应体解析，返回数据格式为：`SelectorList[Selector]`

### `meta`

`property` 类型的方法。返回您在请求中传入的自定义数据

### `cookies`

返回字典类型的 `cookies`，其中

- `key` 为 `cookie` 的 `name`
- `value` 为 `cookie` 的 `value`

### `cookie_list`

返回列表类型的 `cookies`，因某些网站返回的 `ccokies` 中存在多个 `name` 相同的值，所以返回列表类型，方便自定义更精细的处理逻辑。
示例：

```python
[
    {
        "key": "",
        "value": "",
        "domain": "",
        "path": "",
        "expires": "",
        "secure": "",
        "httponly": "",
    },
    ...
]
```
