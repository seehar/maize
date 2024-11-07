from maize import Spider


class BaiduSpider(Spider):
    start_url = "http://www.baidu.com"

    def parse(self, response):
        print(response.text)


if __name__ == "__main__":
    BaiduSpider().run()
