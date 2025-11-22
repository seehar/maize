import asyncio
import typing
from urllib.parse import urlencode

import pytest
from playwright.async_api import Page

from maize import Request, Response, Spider, SpiderSettings
from maize.common.constant.setting_constant import SpiderDownloaderEnum
from maize.downloader.playwright_downloader import PlaywrightDownloader


@pytest.skip(reason="rpa spider", allow_module_level=True)
class DemoRpaSpider(Spider):
    async def start_requests(self) -> typing.AsyncGenerator[Request, typing.Any]:
        for _ in range(1):
            keyword_encode = urlencode({"search_query": "#CoupleVlog"})
            yield Request(f"https://www.youtube.com/results?{keyword_encode}")

    async def parse(self, response: Response[PlaywrightDownloader, Page]):
        self.logger.info(f"原始响应URL:{response.url}")
        self.logger.info(f"响应内容长度:{len(response.text)}")
        self.logger.info("-" * 100)

        try:
            # 使用新的with操作模式获取页面进行操作
            async with response.driver.get_page() as page:
                # 页面已经在downloader中导航到了百度，我们直接操作当前页面
                self.logger.info(f"当前页面URL:{page.url}")

                # 获取页面内容
                content = await page.content()
                self.logger.info(f"页面内容长度:{len(content)}")

                # 检查是否在百度页面
                if "baidu.com" in page.url:
                    # 示例：在搜索框中输入内容
                    search_input = await page.query_selector("//textarea[@id='chat-textarea']")
                    if search_input:
                        await search_input.fill("Playwright并发测试")
                        self.logger.info("成功在搜索框中输入内容")

                        # 点击搜索按钮
                        search_btn = await page.query_selector("//button[@id='chat-submit-button']")
                        if search_btn:
                            await search_btn.click()
                            await page.wait_for_load_state()
                            self.logger.info("成功点击搜索按钮")
                            self.logger.info(f"搜索后页面URL:{page.url}")
                            await asyncio.sleep(3)
                    else:
                        self.logger.info("未找到搜索框，当前页面可能不是百度首页")
                else:
                    self.logger.info(f"当前页面不是百度页面，URL:{page.url}")

                self.logger.info(f"操作完成，页面URL:{page.url}")

        except Exception as e:
            self.logger.error(f"操作页面时出错:{e}")
        finally:
            self.logger.info("-" * 100)


def test_rpa_spider():
    spider_settings = SpiderSettings()
    spider_settings.concurrency = 1
    spider_settings.downloader = SpiderDownloaderEnum.PLAYWRIGHT.value
    spider_settings.logger_handler = "examples.baidu_spider.logger_util.InterceptHandler"
    spider_settings.request.use_session = True
    spider_settings.rpa.headless = True
    spider_settings.rpa.skip_resource_types = ["image", "media", "font", "stylesheet"]
    DemoRpaSpider().run(settings=spider_settings)
