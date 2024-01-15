import typing

import requests
from requests import Response

from maize.core.interface import DownloadInterface


class SyncDownloader(DownloadInterface):
    session = requests.Session()

    def _download_task(
        self, url: str, headers: typing.Optional[dict] = None
    ) -> Response:
        return self.session.get(url, headers=headers or self.headers)
