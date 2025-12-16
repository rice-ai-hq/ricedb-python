"""
RiceDB client exceptions.
"""


class RiceDBError(Exception):
    """Base exception for all RiceDB errors."""

    pass


class ConnectionError(RiceDBError):
    """Raised when unable to connect to RiceDB server."""

    pass


class InsertError(RiceDBError):
    """Raised when document insertion fails."""

    pass


class SearchError(RiceDBError):
    """Raised when search operation fails."""

    pass


class AuthenticationError(RiceDBError):
    """Raised when authentication/authorization fails."""

    pass


class ValidationError(RiceDBError):
    """Raised when input validation fails."""

    pass


class TransportError(RiceDBError):
    """Raised when transport-specific error occurs."""

    pass
