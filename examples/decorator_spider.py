from maize import Spider
from maize import SpiderEntry


spider_entry = SpiderEntry()


@spider_entry.register(settings={"DOWNLOADER": "maize.HTTPXDownloader"})
class DecoratorSpider(Spider):
    start_url = "http://www.baidu.com"

    def parse(self, response):
        print(response.text)


if __name__ == "__main__":
    spider_entry.run()
