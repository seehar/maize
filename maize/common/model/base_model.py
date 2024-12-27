from dataclasses import dataclass
from dataclasses import fields
from pathlib import Path
from typing import Any
from typing import Dict
from typing import Literal
from typing import Union
from typing import get_args
from typing import get_origin
from typing import get_type_hints

import ujson


@dataclass
class BaseModel:
    def __post_init__(self):
        """
        在初始化后自动填充未提供的字段的默认值。
        """
        for field_ in fields(self):
            if (
                getattr(self, field_.name) is None
                and field_.default_factory is not None
            ):
                setattr(self, field_.name, field_.default_factory())

    def get_dict(self) -> Dict[str, Any]:
        return self.__dict__

    @classmethod
    def from_json(cls, json_data: str) -> "BaseModel":
        """
        从 JSON 字符串中解析并创建 SpiderSettings 实例。

        :param json_data: 包含配置的 JSON 字符串
        :return: SpiderSettings 实例
        """
        # 解析 JSON 字符串为字典
        data_dict = ujson.loads(json_data)
        return cls.from_dict(data_dict)

    @classmethod
    def from_dict(cls, data_dict: Dict[str, Any]) -> "BaseModel":
        """
        从字典中解析并创建 SpiderSettings 实例，同时进行类型校验。

        :param data_dict: 包含配置的字典
        :return: SpiderSettings 实例
        """
        # 获取类字段及其默认值和类型提示
        type_hints = get_type_hints(cls)
        validated_data = {}

        for field_ in fields(cls):
            key = field_.name
            expected_type = type_hints.get(key)

            if key not in data_dict:
                if field_.default is not None:
                    validated_data[key] = field_.default
                elif field_.default_factory is not None:
                    validated_data[key] = field_.default_factory()
                else:
                    validated_data[key] = None
                continue
            value = data_dict[key]

            # 类型校验
            origin = get_origin(expected_type)
            args = get_args(expected_type)

            if origin is list and isinstance(value, list):
                if all(isinstance(item, args[0]) for item in value):
                    validated_data[key] = value
                else:
                    try:
                        validated_data[key] = [args[0](item) for item in value]
                    except (ValueError, TypeError):
                        raise ValueError(f"Invalid value for {key}: {value}")
            elif origin is tuple and isinstance(value, (list, tuple)):
                if len(args) == len(value) and all(
                    isinstance(item, arg) for item, arg in zip(value, args)
                ):
                    validated_data[key] = tuple(value)
                else:
                    try:
                        validated_data[key] = tuple(
                            arg(item) for item, arg in zip(value, args)
                        )
                    except (ValueError, TypeError):
                        raise ValueError(f"Invalid value for {key}: {value}")
            elif origin is Union and type(None) in args:
                non_none_args = tuple(arg for arg in args if arg is not type(None))
                if len(non_none_args) == 1:
                    expected_inner_type = non_none_args[0]
                    if value is None or isinstance(value, expected_inner_type):
                        validated_data[key] = value
                    else:
                        try:
                            validated_data[key] = expected_inner_type(value)
                        except (ValueError, TypeError):
                            raise ValueError(f"Invalid value for {key}: {value}")
                else:
                    raise NotImplementedError(
                        "Union types with more than one non-None type are not supported yet."
                    )
            elif origin is Literal:
                if value in args:
                    validated_data[key] = value
                else:
                    raise ValueError(
                        f"Invalid value for {key}: expected one of {args}, got {value}"
                    )
            elif origin is None and isinstance(value, expected_type):
                validated_data[key] = value
            elif expected_type == int and isinstance(value, (int, float)):
                validated_data[key] = int(value)
            elif expected_type == str and isinstance(value, (str, bytes)):
                validated_data[key] = str(value)
            elif expected_type == Path and isinstance(value, (str, Path)):
                validated_data[key] = Path(value)
            else:
                raise TypeError(
                    f"Invalid type for {key}: expected {expected_type}, got {type(value)}: {value}"
                )

        # 创建并返回 SpiderSettings 实例
        instance = cls()
        for field_ in fields(cls):
            if field_.name in validated_data:
                setattr(instance, field_.name, validated_data[field_.name])
            elif field_.default is not None:
                setattr(instance, field_.name, field_.default)
            elif field_.default_factory is not None:
                setattr(instance, field_.name, field_.default_factory())
            else:
                setattr(instance, field_.name, None)

        return instance

    def update_from_dict(self, data_dict: Dict[str, Any]):
        """
        使用字典中的数据更新现有实例的字段值。

        :param data_dict: 包含配置的字典
        """
        type_hints = get_type_hints(type(self))
        for key, value in data_dict.items():
            if hasattr(self, key):
                expected_type = type_hints.get(key)
                origin = get_origin(expected_type)
                args = get_args(expected_type)

                if origin is Literal:
                    if value in args:
                        setattr(self, key, value)
                    else:
                        raise ValueError(
                            f"Invalid value for {key}: expected one of {args}, got {value}"
                        )
                elif origin is list and isinstance(value, list):
                    if all(isinstance(item, args[0]) for item in value):
                        setattr(self, key, value)
                    else:
                        try:
                            setattr(self, key, [args[0](item) for item in value])
                        except (ValueError, TypeError):
                            raise ValueError(f"Invalid value for {key}: {value}")
                elif origin is tuple and isinstance(value, (list, tuple)):
                    if len(args) == len(value) and all(
                        isinstance(item, arg) for item, arg in zip(value, args)
                    ):
                        setattr(self, key, tuple(value))
                    else:
                        try:
                            setattr(
                                self,
                                key,
                                tuple(arg(item) for item, arg in zip(value, args)),
                            )
                        except (ValueError, TypeError):
                            raise ValueError(f"Invalid value for {key}: {value}")
                elif origin is Union and type(None) in args:
                    non_none_args = tuple(arg for arg in args if arg is not type(None))
                    if len(non_none_args) == 1:
                        expected_inner_type = non_none_args[0]
                        if value is None or isinstance(value, expected_inner_type):
                            setattr(self, key, value)
                        else:
                            try:
                                setattr(self, key, expected_inner_type(value))
                            except (ValueError, TypeError):
                                raise ValueError(f"Invalid value for {key}: {value}")
                    else:
                        raise NotImplementedError(
                            "Union types with more than one non-None type are not supported yet."
                        )
                elif origin is None and isinstance(value, expected_type):
                    setattr(self, key, value)
                elif expected_type == int and isinstance(value, (int, float)):
                    setattr(self, key, int(value))
                elif expected_type == str and isinstance(value, (str, bytes)):
                    setattr(self, key, str(value))
                elif expected_type == Path and isinstance(value, (str, Path)):
                    setattr(self, key, Path(value))
                else:
                    raise TypeError(
                        f"Invalid type for {key}: expected {expected_type}, got {type(value)}: {value}"
                    )

    @classmethod
    def from_base_model(cls, base_model: "BaseModel") -> "BaseModel":
        """
        从另一个 BaseModel 实例中解析并创建当前类的实例。

        :param base_model: 包含配置的 BaseModel 实例
        :return: 当前类的实例
        """
        # 将 BaseModel 实例转换为字典
        data_dict = base_model.get_dict()

        # 使用 from_dict 方法创建新实例
        return cls.from_dict(data_dict)
