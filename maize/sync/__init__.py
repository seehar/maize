"""maize 同步爬虫模块。

提供同步版 Lite 和 Classic 爬虫，与 ``maize.aio`` 异步爬虫对应：
- ``maize.sync.lite``: 轻量级同步爬虫（httpx + 线程池）
- ``maize.sync.classic``: 完整同步爬虫（中间件/管道/调度器，httpx 或 requests）
"""
