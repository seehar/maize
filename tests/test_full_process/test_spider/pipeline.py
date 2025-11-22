from maize import BasePipeline, Item


class CustomPipeline(BasePipeline):
    async def open(self):
        """
        管道初始化时调用，需要初始化的异步方法请在此实现
        :return:
        """

    async def close(self):
        """
        管道关闭时调用，需要关闭的异步方法请在此实现
        :return:
        """

    async def process_item(self, items: list["Item"]):
        """
        处理数据，需要处理数据的方法请在此实现。
        为了提高效率，请使用异步方法。
        :param items:
        :return:
        """

    async def process_error_item(self, items: list["Item"]):
        pass
