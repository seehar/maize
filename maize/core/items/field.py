class Field(dict):
    def __init__(self, default=None):
        super().__init__()
        self.default = default
