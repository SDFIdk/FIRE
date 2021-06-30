from uuid import uuid4

__version__ = "1.2.0"


def uuid():
    """UUID generator"""
    return str(uuid4())
