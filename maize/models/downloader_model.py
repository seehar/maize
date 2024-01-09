import typing

from pydantic import BaseModel


class DownLoaderModel(BaseModel):
    url: str
    headers: typing.Optional[dict] = None
    params: typing.Optional[dict] = None
    data: typing.Optional[dict] = None
    proxies: typing.Optional[dict] = None
