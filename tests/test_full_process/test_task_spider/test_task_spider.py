import typing

import pytest

from maize import CrawlerProcess, Request, Response, TaskSpider


class DemoTaskSpider(TaskSpider):
    batch = 1

    async def start_requests(self) -> typing.AsyncGenerator[Request, typing.Any]:
        if self.batch > 2:
            raise StopAsyncIteration

        for _i in range(1):
            yield Request("http://seehar.com")
        self.batch += 1

    async def parse(self, response: Response):
        print(response.text)


@pytest.mark.asyncio
async def test_task_spider():
    process = CrawlerProcess()
    await process.crawl(DemoTaskSpider)
    await process.start()
