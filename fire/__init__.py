"""FIRE - FIkspunktREgister"""

from uuid import uuid4

__version__ = "1.3.1"
__license__ = "MIT"
__author__ = "SDFE, Septima"
__author_email__ = "grf@sdfe.dk"


def uuid():
    """UUID generator"""
    return str(uuid4())
