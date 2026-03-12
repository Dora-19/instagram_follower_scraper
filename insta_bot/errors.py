class AppError(Exception):
    """Base application error."""


class ProviderError(AppError):
    """Raised when provider operations fail."""


class ConfigurationError(AppError):
    """Raised when required configuration is missing."""


class RateLimitError(AppError):
    """Raised when Instagram asks to wait before retrying."""
