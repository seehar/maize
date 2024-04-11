from abc import ABCMeta
from collections.abc import MutableMapping
from copy import deepcopy
from pprint import pformat

from maize.core.items.field import Field
from maize.exceptions.spider_exception import ItemInitException


class ItemMeta(ABCMeta):
    def __new__(mcs, name, bases, attrs):
        cls_instance = super().__new__(mcs, name, bases, attrs)
        cls_instance.FIELDS = {
            key: value for key, value in attrs.items() if isinstance(value, Field)
        }
        return cls_instance


class Item(MutableMapping, metaclass=ItemMeta):
    FIELDS: dict
    __table_name__: str
    __retry_count__: int = 0

    def __init__(self, *args, **kwargs):
        self._values = {}
        if args:
            raise ItemInitException(
                f"Positional arguments are not supported, use keyword arguments."
            )
        for key, value in self.FIELDS.items():
            if key not in kwargs:
                kwargs[key] = value.default
        self.update(kwargs)

    def __setitem__(self, key, value):
        if key not in self.FIELDS:
            raise KeyError(f"{self.__class__.__name__} does not support field: {key}")
        self._values[key] = value

    def __getitem__(self, key):
        return self._values[key]

    def __delitem__(self, key):
        del self._values[key]

    def __setattr__(self, key, value):
        if not key.startswith("_"):
            if key not in self.FIELDS:
                raise AttributeError(
                    f"{self.__class__.__name__} does not support field: {key}"
                )
            self._values[key] = value
        else:
            super().__setattr__(key, value)

    def __getattr__(self, key):
        if key in self.FIELDS:
            if key in self._values:
                return self._values[key]
            else:
                return self.FIELDS[key].default
        else:
            raise AttributeError(
                f"{self.__class__.__name__} does not support field: {key}. "
                f"Please add the '{key}' field to the {self.__class__.__name__} class definition."
            )

    def __getattribute__(self, item):
        field = super().__getattribute__("FIELDS")
        if item in field:
            return self._values.get(item, None)
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

    def retry(self):
        self.__retry_count__ += 1
