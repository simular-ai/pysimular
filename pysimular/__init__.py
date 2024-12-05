"""
Pysimular - Python API for Simular agents
"""

from .browser import SimularBrowser
from .exceptions import SimularError, SimularAPIError, SimularTimeoutError

__version__ = "0.1.0"
__all__ = ["SimularAgent", "SimularError", "SimularAPIError", "SimularTimeoutError"]
