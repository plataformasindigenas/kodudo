"""Exception hierarchy for kodudo."""


class KodudoError(Exception):
    """Base exception for kodudo."""

    pass


class ConfigError(KodudoError):
    """Invalid configuration."""

    pass


class DataError(KodudoError):
    """Cannot load or parse data."""

    pass


class RenderError(KodudoError):
    """Template rendering failed."""

    pass
