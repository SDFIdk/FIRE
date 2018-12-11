from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship

from fireapi.model import RegisteringTidObjekt
from fireapi.model import RegisteringFraObjekt

# TODO: Sag and Sagsevent are supposed to get remodeled into Sag, SagInfo, Sagevent and SageventInfo


class Sag(RegisteringFraObjekt):
    __tablename__ = "sag"
    id = Column(String(36), nullable=False)
    sagsevents = relationship(
        "Sagsevent", order_by="Sagsevent.objectid", back_populates="sag"
    )
    sagsinfos = relationship(
        "Sagsinfo", order_by="Sagsinfo.objectid", back_populates="sag"
    )


class Sagsinfo(RegisteringTidObjekt):
    __tablename__ = "sagsinfo"
    objectid = Column(Integer, primary_key=True)
    aktiv = Column(String(5), nullable=False)
    journalnummer = Column(String)
    behandler = Column(String, nullable=False)
    beskrivelse = Column(String)
    sagid = Column(String, ForeignKey("sag.id"), nullable=False)
    sag = relationship("Sag", back_populates="sagsinfos")


class Sagsevent(RegisteringFraObjekt):
    __tablename__ = "sagsevent"
    id = Column(String(36), nullable=False)
    event = Column(String(4000), nullable=False)
    # beskrivelse = Column(String)
    sagid = Column(String(36), ForeignKey("sag.id"), nullable=False)
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
    observationer = relationship(
        "Observation", order_by="Observation.objectid", back_populates="sagsevent"
    )
    punktinformationer = relationship(
        "PunktInformation",
        order_by="PunktInformation.objectid",
        back_populates="sagsevent",
    )
    beregninger = relationship(
        "Beregning", order_by="Beregning.objectid", back_populates="sagsevent"
    )
