"""FIRE - FIkspunktREgister"""

from uuid import uuid4

__version__ = "1.9.0"
__license__ = "MIT"
__author__ = "SDFI, Septima"
__author_email__ = "grf@sdfi.dk"


def uuid():
    """UUID generator"""
    return str(uuid4())
