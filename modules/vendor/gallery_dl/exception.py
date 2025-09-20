"""Exceptions used by the bundled gallery-dl subset."""

class GalleryDLException(Exception):
    """Base exception mirroring gallery-dl's error hierarchy."""


class HttpError(GalleryDLException):
    """Raised when a HTTP request to nhentai fails."""

    def __init__(self, status_code: int, message: str = "") -> None:
        self.status_code = status_code
        super().__init__(message or f"HTTP request failed with status {status_code}")
