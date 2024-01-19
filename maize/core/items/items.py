from abc import ABCMeta
from collections.abc import MutableMapping
from copy import deepcopy
from pprint import pformat

from maize.core.items.field import Field
from maize.exceptions.spider_exception import ItemAttributeException
from maize.exceptions.spider_exception import ItemInitException


class ItemMeta(ABCMeta):
    def __new__(mcs, name, bases, attrs):
        field = {}
        for key, value in attrs.items():
            if isinstance(value, Field):
                field[key] = value

        cls_instance = super().__new__(mcs, name, bases, attrs)
        cls_instance.FIELDS = field
        return cls_instance


class Item(MutableMapping, metaclass=ItemMeta):
    FIELDS: dict

    def __init__(self, *args, **kwargs):
        self._values = {}
        if args:
            raise ItemInitException(
                f"{self.__class__.__name__}: position args is not supported, use keyword args"
            )

        if kwargs:
            for key, value in kwargs.items():
                self[key] = value

    def __setitem__(self, key, value):
        if key not in self.FIELDS:
            raise KeyError(f"{self.__class__.__name__} does not support field")

        self._values[key] = value

    def __getitem__(self, key):
        return self._values[key]

    def __delitem__(self, key):
        del self._values[key]

    def __setattr__(self, key, value):
        if not key.startswith("_"):
            raise AttributeError(f"use item[{key!r}] = {value!r} to set field value")

        super().__setattr__(key, value)

    def __getattr__(self, key):
        raise AttributeError(
            f"{self.__class__.__name__} does not support field: {key}. "
            f"please add the `{key}` field to the {self.__class__.__name__}, "
            f"and use item[{key!r}] to get field value"
        )

    def __getattribute__(self, item):
        field = super().__getattribute__("FIELDS")
        if item in field:
            raise ItemAttributeException(f"use item[{item!r}] to get field value")

        return super().__getattribute__(item)

    def __repr__(self):
        return pformat(dict(self))

    __str__ = __repr__

    def __iter__(self):
        return iter(self._values)

    def __len__(self):
        return len(self._values)

    def to_dict(self) -> dict:
        return dict(self)

    def copy(self) -> "Item":
        return deepcopy(self)
