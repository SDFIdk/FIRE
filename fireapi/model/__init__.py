"""SQLAlchemy models for the application
"""
import sqlalchemy.ext.declarative
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from . import columntypes


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
    registreringfra = Column(DateTime(timezone=True), nullable=False)
    registreringtil = Column(DateTime(timezone=True))


class Sag(RegisteringTidObjekt):
    __tablename__ = "sag"
    id = Column(String, nullable=False)
    journalnummer = Column(String)
    behandler = Column(String, nullable=False)
    beskrivelse = Column(String)
    sagsevents = relationship("Sagsevent", order_by="Sagsevent.objectid", back_populates="sag")
    # TODO: Sagstype


class Sagsevent(RegisteringTidObjekt):
    __tablename__ = "sagsevent"
    id = Column(String, nullable=False)
    event = Column(String, nullable=False)
    beskrivelse = Column(String)
    sagid = Column(Integer, ForeignKey('sag.objectid'), nullable=False)
    sag = relationship("Sag", back_populates="sagsevents")
    # TODO: Eventtype, materiale, and rapporthtml
    # Fikspunktregisterobjekter
    punkter = relationship("Punkt", order_by="Punkt.objectid", back_populates="sagsevent")
    koordinater = relationship("Koordinat", order_by="Koordinat.objectid", back_populates="sagsevent")
    geometriobjekter = relationship("GeometriObjekt", order_by="GeometriObjekt.objectid", back_populates="sagsevent")
    # TODO: Beregninger, Observationer, PunktInfoer


# -------------------------------------------------------------
# Fikspunktregisterobjekter
# -------------------------------------------------------------


class FikspunktregisterObjekt(RegisteringTidObjekt):
    __abstract__ = True


class Punkt(FikspunktregisterObjekt):
    __tablename__ = "punkt"
    id = Column(String, nullable=False, unique=True)
    sagseventid = Column(Integer, ForeignKey('sagsevent.objectid'), nullable=False)
    sagsevent = relationship("Sagsevent", back_populates="punkter")
    koordinater = relationship("Koordinat", order_by="Koordinat.objectid", back_populates="punkt")
    geometriobjekter = relationship("GeometriObjekt", order_by="GeometriObjekt.objectid", back_populates="punkt")
    # TODO: Observationer, PunktInfoer


class Koordinat(FikspunktregisterObjekt):
    __tablename__ = "koordinat"
    srid = Column(String, nullable=False)
    # TODO: srid is foreign key constrained
    sx = Column(Float)
    sy = Column(Float)
    sz = Column(Float)
    t = Column(DateTime(timezone=True))
    transformeret = Column(String, nullable=False)
    x = Column(Float)
    y = Column(Float)
    z = Column(Float)
    sagseventid = Column(Integer, ForeignKey('sagsevent.objectid'), nullable=False)
    sagsevent = relationship("Sagsevent", back_populates="koordinater")
    punktid = Column(Integer, ForeignKey('punkt.objectid'), nullable=False)
    punkt = relationship("Punkt", back_populates="koordinater")
    # TODO: beregninger


class GeometriObjekt(FikspunktregisterObjekt):
    __tablename__ = "geometriobjekt"
    geometri = Column(columntypes.Point(2, 4326), nullable=False)
    sagseventid = Column(Integer, ForeignKey('sagsevent.objectid'), nullable=False)
    sagsevent = relationship("Sagsevent", back_populates="geometriobjekter")
    punktid = Column(Integer, ForeignKey('punkt.objectid'), nullable=False)
    punkt = relationship("Punkt", back_populates="geometriobjekter")


