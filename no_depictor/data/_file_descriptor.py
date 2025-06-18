class FileDescriptor:

    def __init__(self, mId: str, title: str):
        self.mId = mId
        self.title = title # With namespace


    def __iter__(self):
        return iter((self.mId, self.title))
