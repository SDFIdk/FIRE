from uuid import uuid4

__version__ = "1.0.0-alpha1"


def uuid():
    """UUID generator"""
    return str(uuid4())
