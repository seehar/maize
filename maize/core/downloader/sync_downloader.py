import typing

import requests
from requests import Response

from maize.core.interface import DownloadInterface


class SyncDownloader(DownloadInterface):
    session = requests.Session()

    def download(self, url: str, headers: typing.Optional[dict] = None) -> Response:
        response = super().download(url, headers)
        if not self.verify(url, response):
            raise Exception("Download verify failed")
        return response

    def _download_task(
        self, url: str, headers: typing.Optional[dict] = None
    ) -> Response:
        return self.session.get(url, headers=headers or self.headers, verify=False)

    def verify(self, url: str, response) -> bool:
        return True
