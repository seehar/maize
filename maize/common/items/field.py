"""
数据项字段定义。

将 Pydantic 的 ``Field`` 重新导出为 :data:`Field`，
供 :class:`~maize.common.items.items.Item` 子类声明字段时使用。
"""

from pydantic import Field as PydanticField

Field = PydanticField
