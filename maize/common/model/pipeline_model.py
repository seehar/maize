from maize.common.model.base_model import BaseModel


class PipelineProcessResult(BaseModel):
    success_count: int = 0
    fail_count: int = 0

    def add(self, result: "PipelineProcessResult"):
        self.success_count += result.success_count
        self.fail_count += result.fail_count
