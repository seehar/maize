import pytest

from maize.core.downloader import SyncDownloader


@pytest.mark.asyncio
class TestSyncDownloader:
    async def test_download(self):
        url = "http://www.seehar.com"
        downloader = SyncDownloader()
        response = downloader.download(url)
        assert response.status_code == 200
        assert response.text.startswith("<!DOCTYPE html>")
