# 相应 - Response

## 简介

`Response` 为 `maize` 为适配不同下载器对响应进行的封装。
爬虫 `parse` 方法中，会返回 `Response` 类型的参数，您可以对响应进行对应对解析和处理

## 参数详解

```text
@param url: url
@param headers: 响应头
@param request: 请求 Response
@param body: 响应体 bytes 类型
@param status: 响应状态码，如 200
```

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
