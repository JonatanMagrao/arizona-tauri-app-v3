class AppBaseError(Exception):
    """Exceção base para erros customizados do app."""

    def __init__(self, message: str, code: str = "error"):
        super().__init__(message)
        self.message = message
        self.code = code

class IDError(AppBaseError):
    def __init__(self, message: str, code: str = "error"):
        super().__init__(message, code)

