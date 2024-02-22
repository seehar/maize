# 简介及安装

> maize 是一个基于异步，轻量级 Python 爬虫框架

## 环境要求

- Python 3.10+
- Linux, Windows, macOS

## 安装

=== "pip"
    ```shell
    pip install maize
    ```

=== "poetry"
    ```shell
    poetry add maize
    ```

## 爬虫示例

```python
from maize import Spider, SpiderEntry


spider_entry = SpiderEntry()


@spider_entry.register()
class DecoratorSpider(Spider):
    start_url = "http://www.baidu.com"

    def parse(self, response):
        print(response.text)


if __name__ == "__main__":
    spider_entry.run()
```
