from collections.abc import MutableMapping
from copy import deepcopy
from typing import Any
from typing import Optional
from typing import Type
from typing import Union

from maize.settings.spider_settings import SpiderSettings


class SettingsManager(MutableMapping):
    def __init__(self, values: Optional[dict] = None):
        self.attributes = {}
        self.set_settings(SpiderSettings)
        self.update_values(values)

    def __getitem__(self, item: str):
        if item not in self:
            return None
        return self.attributes[item]

    def __contains__(self, item: str):
        return item in self.attributes

    def __setitem__(self, key: str, value: Any):
        self.set(key, value)

    def __delitem__(self, key: str):
        self.delete(key)

    def __str__(self):
        return f"<Settings values={self.attributes}>"

    __repr__ = __str__

    def __iter__(self):
        return iter(self.attributes)

    def __len__(self):
        return len(self.attributes)

    def set(self, key: str, value: Any):
        self.attributes[key] = value

    def delete(self, key: str):
        del self.attributes[key]

    def get(self, name: str, default: Any = None) -> Any:
        return self[name] if self[name] is not None else default

    def getint(self, name: str, default: int = 0) -> int:
        return int(self.get(name, default))

    def getfloat(self, name: str, default: float = 0.0) -> float:
        return float(self.get(name, default))

    def getbool(self, name: str, default: bool = False) -> bool:
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

    def getlist(self, name: str, default: Optional[list] = None) -> list:
        got = self.get(name, default or [])
        if isinstance(got, str):
            got = got.split(",")
        return list(got)

    def set_settings(self, module: Union[str, Type["SpiderSettings"]]):
        if isinstance(module, str):
            from maize.utils.project_util import load_class

            module = load_class(module)

        for key in dir(module):
            if key.isupper():
                self.set(key, getattr(module, key))

    def update_values(self, values: Optional[dict]):
        if values is None:
            return

        for key, value in values.items():
            self.set(key, value)

    def copy(self):
        return deepcopy(self)

    @property
    def redis_url(self):
        redis_url_username_password = ""
        if self.get("REDIS_USERNAME") or self.get("REDIS_PASSWORD"):
            redis_url_username_password = f"{self.get('REDIS_USERNAME') or ''}:{self.get('REDIS_PASSWORD') or ''}@"

        return f"redis://{redis_url_username_password}{self.get('REDIS_HOST')}:{self.get('REDIS_PORT')}/{self.get('REDIS_DB')}"
