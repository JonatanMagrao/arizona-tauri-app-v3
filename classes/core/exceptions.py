class AppBaseError(Exception):
    """Exceção base para erros customizados do app."""

    def __init__(self, message: str, code: str = "error"):
        super().__init__(message)
        self.message = message
        self.code = code

class IDError(AppBaseError):
    def __init__(self, message: str, code: str = "error"):
        super().__init__(message, code)

class MediaFileNotFoundError(AppBaseError):
    def __init__(self, message: str, code: str = "error"):
        super().__init__(message, code)

class LinkDataRetrievalError(AppBaseError):
    def __init__(self, original_error: str):
        message = f"Failed to retrieve link data from Google Drive API: {original_error}"
        super().__init__(message, code="LINK_DATA_ERROR")

class InvalidURL(AppBaseError):
    def __init__(self, url):
        super().__init__(f"Invalid URL: {url}", code="INVALID_URL")

class GoogleSheetLogError(AppBaseError):
    def __init__(self,url):
        super().__init__(f"Failed to log to Google Sheet: {url}", code="GOOGLE_SHEET_LOG_ERROR")