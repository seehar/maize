import typing
from abc import ABC
from abc import abstractmethod


class DownloadInterface(ABC):
    headers: dict[str, str] = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/111.0.0.0 Safari/537.36",
    }

    def __init__(self):
        pass

    def download(self, url: str, headers: typing.Optional[dict] = None):
        response = self._download_task(url, headers or self.headers)

        if not self.verify(url, response):
            raise Exception("Download failed")
        return response

    @abstractmethod
    def _download_task(self, url: str, headers: typing.Optional[dict] = None):
        raise NotImplementedError

    def verify(self, url: str, response) -> bool:
        return True
