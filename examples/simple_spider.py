from maize import Response
from maize import Spider
from maize import SpiderSettings


class BaiduSpider(Spider):
    def __init__(self):
        super().__init__()
        self.start_url = "http://www.baidu.com"

    def parse(self, response: Response):
        self.logger.info(f"响应状态码: {response.status}")
        self.logger.info(f"响应内容: {response.text[:100]}...")


if __name__ == "__main__":
    settings = SpiderSettings(
        project_name="百度爬虫",
    )

    BaiduSpider().run(settings)
