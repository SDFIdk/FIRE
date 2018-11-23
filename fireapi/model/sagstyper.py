from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship

from . import RegisteringTidObjekt


class Sag(RegisteringTidObjekt):
    __tablename__ = "sag"
    id = Column(String, nullable=False)
    journalnummer = Column(String)
    behandler = Column(String, nullable=False)
    beskrivelse = Column(String)
    sagsevents = relationship(
        "Sagsevent", order_by="Sagsevent.objectid", back_populates="sag"
    )
    # TODO: Sagstype


class Sagsevent(RegisteringTidObjekt):
    __tablename__ = "sagsevent"
    id = Column(String, nullable=False)
    event = Column(String, nullable=False)
    beskrivelse = Column(String)
    sagid = Column(Integer, ForeignKey("sag.objectid"), nullable=False)
    sag = relationship("Sag", back_populates="sagsevents")
    # TODO: Eventtype, materiale, and rapporthtml
    # Fikspunktregisterobjekter
    punkter = relationship(
        "Punkt", order_by="Punkt.objectid", back_populates="sagsevent"
    )
    koordinater = relationship(
        "Koordinat", order_by="Koordinat.objectid", back_populates="sagsevent"
    )
    geometriobjekter = relationship(
        "GeometriObjekt", order_by="GeometriObjekt.objectid", back_populates="sagsevent"
    )
    # TODO: Beregninger, Observationer, PunktInfoer
