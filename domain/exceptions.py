class DomainException(Exception):
    """Base class for all domain-specific exceptions."""
    pass

class ConfigurationError(DomainException):
    """Raised when application configuration is invalid or incomplete."""
    pass

class RegistryError(DomainException):
    """Raised when adapter registration or lookup fails."""
    pass

class TranscriberError(DomainException):
    """Raised when transcription fails inside an adapter."""
    pass

class SummarizerError(DomainException):
    """Raised when summarization fails inside an adapter."""
    pass

class StructurizerError(DomainException):
    """Raised when structuring fails inside an adapter."""
    pass

class StorageError(DomainException):
    """Raised when storage load/save operations fail."""
    pass

class SessionNotFoundError(StorageError):
    """Raised when a requested session cannot be found in storage."""
    pass
