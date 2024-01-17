import typing
from collections.abc import MutableMapping
from copy import deepcopy
from importlib import import_module

from maize.core.settings import default_settings


class SettingsManager(MutableMapping):
    def __init__(self, values: typing.Optional[dict] = None):
        self.attributes = {}
        self.set_settings(default_settings)
        self.update_values(values)

    def __getitem__(self, item):
        if item not in self:
            return None
        return self.attributes[item]

    def get(self, name, default=None):
        return self[name] if self[name] is not None else default

    def getint(self, name, default: int = 0) -> int:
        return int(self.get(name, default))

    def getfloat(self, name, default: float = 0.0) -> float:
        return float(self.get(name, default))

    def getbool(self, name, default: bool = False) -> bool:
        got = self.get(name, default)
        try:
            return bool(int(got))
        except ValueError:
            if got in ("true", "True", "TRUE"):
                return True
            if got in ("false", "False", "FALSE"):
                return False
            raise ValueError(
                "supported values for bool are (0 or 1), (True or False), ('0' or '1'), "
                "('True' or 'False'), ('true' or 'false'), ('TRUE', 'FALSE')"
            )

    def getlist(self, name, default=None) -> list:
        got = self.get(name, default or [])
        if isinstance(got, str):
            got = got.split(",")
        return list(got)

    def __contains__(self, item):
        return item in self.attributes

    def __setitem__(self, key, value):
        self.set(key, value)

    def set(self, key, value):
        self.attributes[key] = value

    def __delitem__(self, key):
        self.delete(key)

    def delete(self, key):
        del self.attributes[key]

    def set_settings(self, module):
        if isinstance(module, str):
            module = import_module(module)
        for key in dir(module):
            if key.isupper():
                self.set(key, getattr(module, key))

    def __str__(self):
        return f"<Settings values={self.attributes}>"

    __repr__ = __str__

    def update_values(self, values: typing.Optional[dict]):
        if values is None:
            return

        for key, value in values.items():
            self.set(key, value)

    def __iter__(self):
        return iter(self.attributes)

    def __len__(self):
        return len(self.attributes)

    def copy(self):
        return deepcopy(self)
