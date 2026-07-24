"""
同步下载器，支持 httpx 和 requests 两种实现。
"""

from maize.sync.classic.downloader.sync_base_downloader import SyncBaseDownloader
from maize.sync.classic.downloader.sync_httpx_downloader import SyncHttpxDownloader
from maize.sync.classic.downloader.sync_requests_downloader import SyncRequestsDownloader

__all__ = ["SyncBaseDownloader", "SyncHttpxDownloader", "SyncRequestsDownloader"]
