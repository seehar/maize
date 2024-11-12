from maize import Spider


class BaiduSpider(Spider):
    start_url = "http://www.baidu.com"
    custom_settings = {
        "USE_REDIS": True,
        "REDIS_HOST": "192.168.137.219",
        "REDIS_PORT": 6379,
        "REDIS_DB": 0,
        "REDIS_USERNAME": None,
        "REDIS_PASSWORD": "123456",
    }

    def parse(self, response):
        print(response.text)


if __name__ == "__main__":
    BaiduSpider().run()
