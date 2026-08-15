"""Application-specific exceptions."""


class VideoEditingError(RuntimeError):
    """Base error for expected pipeline failures."""


class ConfigurationError(VideoEditingError):
    """Raised when a configuration file cannot be loaded."""
