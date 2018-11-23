"""SQLAlchemy models for the application
"""
import sqlalchemy.ext.declarative
from sqlalchemy import Column, Integer, DateTime, func


class ReprBase(object):
    """Extend the base class
    Provides a nicer representation when a class instance is printed.
    Found on the SA wiki
    """

    def __repr__(self):
        return "%s(%s)" % (
            (self.__class__.__name__),
            ", ".join(
                [
                    "%s=%r" % (key, getattr(self, key))
                    for key in sorted(self.__dict__.keys())
                    if not key.startswith("_")
                ]
            ),
        )


# base class for SQLAlchemy declarative models. Inherits ReprBase to get nicer __repr__ behaviour
DeclarativeBase = sqlalchemy.ext.declarative.declarative_base(cls=ReprBase)


class RegisteringTidObjekt(DeclarativeBase):
    # SQLALchemy knows abstract classes do not map to a table.
    # If class is not declared abstract then SQLAlchemy whines about missing table declaration.
    __abstract__ = True
    objectid = Column(Integer, primary_key=True)
    registreringfra = Column(
        DateTime(timezone=True), nullable=False, default=func.sysdate()
    )
    registreringtil = Column(DateTime(timezone=True))


# Expose these types
from .geometry import *
from .punkttyper import *
from .sagstyper import *
