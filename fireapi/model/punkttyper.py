from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from . import RegisteringTidObjekt, columntypes

# Eksports
__all__ = ["FikspunktregisterObjekt", "Punkt", "Koordinat", "GeometriObjekt"]


class FikspunktregisterObjekt(RegisteringTidObjekt):
    __abstract__ = True


class Punkt(FikspunktregisterObjekt):
    __tablename__ = "punkt"
    id = Column(String, nullable=False, unique=True)
    sagseventid = Column(Integer, ForeignKey("sagsevent.objectid"), nullable=False)
    sagsevent = relationship("Sagsevent", back_populates="punkter")
    koordinater = relationship(
        "Koordinat", order_by="Koordinat.objectid", back_populates="punkt"
    )
    geometriobjekter = relationship(
        "GeometriObjekt", order_by="GeometriObjekt.objectid", back_populates="punkt"
    )
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
    sagseventid = Column(Integer, ForeignKey("sagsevent.objectid"), nullable=False)
    sagsevent = relationship("Sagsevent", back_populates="koordinater")
    punktid = Column(Integer, ForeignKey("punkt.objectid"), nullable=False)
    punkt = relationship("Punkt", back_populates="koordinater")
    # TODO: beregninger


class GeometriObjekt(FikspunktregisterObjekt):
    __tablename__ = "geometriobjekt"
    geometri = Column(columntypes.Point(2, 4326), nullable=False)
    sagseventid = Column(Integer, ForeignKey("sagsevent.objectid"), nullable=False)
    sagsevent = relationship("Sagsevent", back_populates="geometriobjekter")
    punktid = Column(Integer, ForeignKey("punkt.objectid"), nullable=False)
    punkt = relationship("Punkt", back_populates="geometriobjekter")
