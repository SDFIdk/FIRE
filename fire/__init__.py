from uuid import uuid4

__version__ = "0.3.0"


def uuid():
    """UUID generator"""
    return str(uuid4())
