"""
Pydantic 基础模型。

对 :class:`pydantic.BaseModel` 的薄封装，作为框架内所有数据模型的统一基类。
"""

from pydantic import BaseModel as PydanticBaseModel


class BaseModel(PydanticBaseModel):
    """
    框架数据模型基类，继承自 Pydantic BaseModel。
    """

    ...
