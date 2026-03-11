class AppError(Exception):
    """Base application error."""


class ProviderError(AppError):
    """Raised when provider operations fail."""


class ConfigurationError(AppError):
    """Raised when required configuration is missing."""
