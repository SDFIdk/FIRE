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
    punktinformationer = relationship(
        "PunktInformation", order_by="PunktInformation.objectid", back_populates="punkt"
    )
    # TODO: Observationer (Note Observation has three references to Punkt. How to handle this?)


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


class Observation(FikspunktregisterObjekt):
    __tablename__ = "observation"
    value1 = Column(Float, nullable=False)
    value2 = Column(Float)
    value3 = Column(Float)
    value4 = Column(Float)
    value5 = Column(Float)
    value6 = Column(Float)
    value7 = Column(Float)
    value8 = Column(Float)
    value9 = Column(Float)
    value10 = Column(Float)
    value11 = Column(Float)
    value12 = Column(Float)
    value13 = Column(Float)
    value14 = Column(Float)
    value15 = Column(Float)
    sagseventid = Column(Integer, ForeignKey("sagsevent.objectid"), nullable=False)
    sagsevent = relationship("Sagsevent", back_populates="observationer")
    antal = Column(Integer, nullable=False)
    gruppe = Column(Integer)
    # TODO: observationstype is foreign key
    observationstype = Column(String, nullable=False)
    sigtepunktid1 = Column(Integer, ForeignKey("punkt.objectid"))
    sigtepunkt1 = relationship("Punkt", foreign_keys=[sigtepunktid1])
    sigtepunktid2 = Column(Integer, ForeignKey("punkt.objectid"))
    sigtepunkt2 = relationship("Punkt", foreign_keys=[sigtepunktid2])
    opstillingspunktid = Column(Integer, ForeignKey("punkt.objectid"))
    opstillingspunkt = relationship("Punkt", foreign_keys=[opstillingspunktid])


class PunktInformation(FikspunktregisterObjekt):
    __tablename__ = "punktinfo"
    sagseventid = Column(Integer, ForeignKey("sagsevent.objectid"), nullable=False)
    sagsevent = relationship("Sagsevent", back_populates="punktinformationer")
    # TODO: Infotype is foreign key
    infotype = Column(String, nullable=False)
    reeltal = Column(Float)
    tekst = Column(String)
    punktid = Column(Integer, ForeignKey("punkt.objectid"), nullable=False)
    punkt = relationship("Punkt", back_populates="punktinformationer")
