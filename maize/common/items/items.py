from maize.common.model.base_model import BaseModel


class Item(BaseModel):
    __table_name__: str = ""
    __retry_count__: int = 0

    def retry(self):
        self.__retry_count__ += 1
