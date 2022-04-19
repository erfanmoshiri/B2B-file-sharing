class Message:

    def __init__(self, _type: str, message: dict, listens_on_port=None, file=None, encode=False):
        self._type = _type
        self.message = message
        self.listens_on_port = listens_on_port
        self.file = file
        self.encode = encode
