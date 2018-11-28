from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship

from . import RegisteringTidObjekt
from . import RegisteringFraObjekt
from . import FikspunktregisterObjekt

# TODO: Sag and Sagsevent are supposed to get remodeled into Sag, SagInfo, Sagevent and SageventInfo


class Sag(RegisteringTidObjekt):
    __tablename__ = "sag"
    # TODO: Sagstype is foreign key
#    sagstype = Column(String, nullable=False)
    id = Column(String, nullable=False)
#    journalnummer = Column(String)
#    behandler = Column(String, nullable=False)
#    beskrivelse = Column(String)
    sagsevents = relationship(
        "Sagsevent", order_by="Sagsevent.objectid", back_populates="sag"
    )


class Sagsevent(RegisteringFraObjekt):
    __tablename__ = "sagsevent"
    id = Column(String, nullable=False)
    event = Column(String, nullable=False)
    #beskrivelse = Column(String)
    sagid = Column(String, ForeignKey("sag.id"), nullable=False)
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
        "Beregning",
        order_by="Beregning.objectid",
        back_populates="sagsevent"
    )
    # TODO: Beregninger
