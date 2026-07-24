# Docstring 规范（reStructuredText 格式）

## 基本格式

- 所有 docstring 使用三引号 `"""`，开头 `"""` 必须单独占一行
- 结尾 `"""` 也单独占一行
- 第一行为一句话概述（句尾加句号）
- 概述与详细说明之间空一行
- 详细说明与字段标签（`:param:` 等）之间空一行

## 模块级

文件顶部，一句话说明模块职责，可补充实现细节或与其他模块的关系。

```python
"""
同步爬虫优先级队列。

基于 `queue.PriorityQueue` 实现，用于同步 Classic 引擎的请求调度。
与异步版 `SpiderPriorityQueue` 对应：min-heap，priority 数值越小越优先出队。
"""
```

## 类级

一句话概述 + 空行 + 补充说明（可选）+ `:param:` 列出构造参数。

```python
class SyncSpiderPriorityQueue:
    """
    同步优先级队列，按 Request.priority 升序出队。

    内部用 ``(priority, counter, request)`` 三元组入队，counter 保证
    同优先级时 FIFO，避免 Request 对象之间直接比较。

    :param maxsize: 队列最大容量，0 表示不限，默认 0
    """
```

## 方法 / 函数级

一句话概述 + 空行 + 补充说明（可选）+ 字段标签。

```python
def get_by_priority(self, gte_priority: int, timeout: float | None = 0.1) -> "Request | None":
    """
    获取优先级大于等于指定值的请求，不满足则放回队列。

    :param gte_priority: 最低优先级阈值（数值越大优先级越低）
    :param timeout: 等待超时时间（秒），默认 0.1
    :return: 满足条件的请求，不满足或超时则返回 None
    """
```

## property

一句话即可；行为复杂时加空行补充。

```python
@property
def max_depth(self) -> int:
    """
    最大爬取深度，0 表示不限。

    start_requests 产出的请求为 depth=0，parse 中 yield 的 Request
    每跟进一层 depth + 1。超过 max_depth 的请求会被丢弃。
    """
```

## 字段标签速查

| 标签 | 用途 |
|---|---|
| `:param name:` | 参数说明 |
| `:type name:` | 参数类型（有类型注解时可省略） |
| `:return:` | 返回值说明 |
| `:rtype:` | 返回值类型（有类型注解时可省略） |
| `:raises ExcType:` | 可能抛出的异常 |
| `:ivar name:` | 实例属性说明（类 docstring 中使用） |

## 覆盖要求

- 所有公共类、公共方法、`__init__` 必须有 docstring
- 模块文件必须有模块级 docstring
- 私有方法（`_` 前缀）如果逻辑非显而易见，也应添加
- 纯透传 / 单行 return 的私有方法可省略

## 类型引用

- 行内引用用双反引号：`` ``Request`` ``
- 需要 Sphinx 交叉引用时用：`:class:`~maize.common.http.Request``

## 语言

- 使用中文撰写
- 技术术语保留英文原文（如 min-heap、FIFO、timeout）
