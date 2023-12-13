

class OpenaiException(BaseException):
    """Исключение для неудачного ответа на запросы OpenAI."""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
