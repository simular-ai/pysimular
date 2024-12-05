"""
Exceptions for the pysimular package
"""


class SimularError(Exception):
    """Base exception for all pysimular errors."""

    pass


class SimularAPIError(SimularError):
    """Raised when an API request fails."""

    pass


class SimularTimeoutError(SimularError):
    """Raised when an API request times out."""

    pass
