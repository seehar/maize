from collections.abc import AsyncGenerator
from typing import Any

from maize import Request, Spider, SpiderEntry
from maize.common.constant.setting_constant import SpiderDownloaderEnum

spider_entry = SpiderEntry()


@spider_entry.register(settings={"downloader": SpiderDownloaderEnum.HTTPX.value})
class DecoratorSpider(Spider):
    async def start_requests(self) -> AsyncGenerator[Request, Any]:
        yield Request(url="http://www.baidu.com")

    def parse(self, response):
        print(response.text)


if __name__ == "__main__":
    spider_entry.run()
