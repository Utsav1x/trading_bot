class TradingBotError(Exception):
    """Base class for application exceptions."""


class ValidationError(TradingBotError):
    """Raised when CLI or order inputs are invalid."""


class NetworkError(TradingBotError):
    """Raised when the Binance API is unreachable."""


class APIError(TradingBotError):
    """Raised when Binance API returns an error response."""

    def __init__(self, message: str, status_code: int | None = None, code: int | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.code = code

