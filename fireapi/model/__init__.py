"""SQLAlchemy models for the application
"""
import sqlalchemy.ext.declarative
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship


class ReprBase(object):
    """Extend the base class
    Provides a nicer representation when a class instance is printed.
    Found on the SA wiki
    """

    def __repr__(self):
        return "%s(%s)" % (
            (self.__class__.__name__),
            ', '.join(["%s=%r" % (key, getattr(self, key))
                       for key in sorted(self.__dict__.keys())
                       if not key.startswith('_')]))


# base class for SQLAlchemy declarative models. Inherits ReprBase to get nicer __repr__ behaviour
DeclarativeBase = sqlalchemy.ext.declarative.declarative_base(cls=ReprBase)


class RegisteringTidObjekt(DeclarativeBase):
    # SQLALchemy knows abstract classes do not map to a table.
    # If class is not declared abstract then SQLAlchemy whines about missing table declaration.
    __abstract__ = True
    objectid = Column(Integer, primary_key=True)
    registreringfra = Column(DateTime(timezone=True))
    registreringtil = Column(DateTime(timezone=True))


class Sag(RegisteringTidObjekt):
    __tablename__ = "sag"
    id = Column(String)
    sagsevents = relationship("Sagsevent", order_by="Sagsevent.objectid", back_populates="sag")
    # TODO


class Sagsevent(RegisteringTidObjekt):
    __tablename__ = "sagsevent"
    id = Column(String)
    sagid = Column(Integer, ForeignKey('sag.objectid'))
    sag = relationship("Sag", back_populates="sagsevents")
    # TODO


class FikspunktregisterObjekt(RegisteringTidObjekt):
    __abstract__ = True
    # TODO: Hvordan nedarver vi en foreign relation til sagsevent?


class Punkt(FikspunktregisterObjekt):
    __tablename__ = "punkt"
    id = Column(String)
    # fullname = Column(String)
    # password = Column(String)

