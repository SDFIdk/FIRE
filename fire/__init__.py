from uuid import uuid4

__version__ = "1.2.1"


def uuid():
    """UUID generator"""
    return str(uuid4())
