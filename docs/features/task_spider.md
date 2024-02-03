# TaskSpider 任务爬虫

> 实际应用中，可能会存在需要持续性的获取采集任务，每批任务采集完成后，再次从数据源获取或者生成一批新的采集任务的情况。
> 此时，使用任务爬虫 `TaskSpider` 代替 `Spider` 普通爬虫，是一个更优的选择。
> 
> 任务爬虫在 [Spider](./spider.md) 的基础上，增加了分批获取任务的能力。


## 简介

会自动调用 `task_requests` 方法获取任务，用户需要重写 `task_requests` 方法，返回任务列表。
当 `task_requests` 无任务时，需要抛出 `StopAsyncIteration` 异常来结束任务获取。


## 使用

这是一个简单的任务爬虫示例：

```python
import asyncio
import typing

from maize import CrawlerProcess, Request, Response, TaskSpider


class DemoTaskSpider(TaskSpider):
    batch = 1
    start_urls = []

    async def task_requests(self) -> typing.AsyncGenerator[Request, typing.Any]:
        # 使用 batch 模拟是否有更多采集任务，实际开发中，您无需使用 batch 变量
        if self.batch > 2:
            # 无更多采集任务，抛出 StopAsyncIteration 异常来结束任务获取
            raise StopAsyncIteration

        for i in range(1):
            yield Request("http://seehar.com")
        self.batch += 1

    async def parse(self, response: Response):
        print(response.text)

        
async def run():
    process = CrawlerProcess()
    await process.crawl(DemoTaskSpider)
    await process.start()


if __name__ == '__main__':
    asyncio.run(run())
```
