from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Any

from maize.base.interface.spider_interface import SpiderInterface

if TYPE_CHECKING:
    from maize import Request, Response


class LiteSpiderInterface(SpiderInterface, ABC):
    @abstractmethod
    async def open(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def close(self) -> None:
        pass

    @abstractmethod
    async def start_requests(self) -> AsyncGenerator["Request", Any]:
        pass

    @abstractmethod
    async def parse(self, response: "Response"):
        pass
