"""Safe, user-facing application errors."""


class AppError(Exception):
    """An expected error that can be returned to an MCP client safely."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class ConfigurationError(AppError):
    """The server is missing required runtime configuration."""

    def __init__(self, message: str) -> None:
        super().__init__("configuration_error", message)


class InvalidInputError(AppError):
    """A tool input failed validation."""

    def __init__(self, message: str) -> None:
        super().__init__("invalid_input", message)


class InvalidUrlError(AppError):
    """A URL is not safe or supported."""

    def __init__(self, message: str) -> None:
        super().__init__("invalid_url", message)


class UpstreamError(AppError):
    """An upstream service failed without exposing internal details."""

    def __init__(self, message: str, code: str = "upstream_error") -> None:
        super().__init__(code, message)