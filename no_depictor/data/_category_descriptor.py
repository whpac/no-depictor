class CategoryDescriptor:

    def __init__(self, qId: str, title: str):
        self.qId = qId
        self.title = title # Without namespace


    def __iter__(self):
        return iter((self.qId, self.title))
