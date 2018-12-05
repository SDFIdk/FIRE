from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship

from . import RegisteringTidObjekt
from . import RegisteringFraObjekt
from . import FikspunktregisterObjekt

# TODO: Sag and Sagsevent are supposed to get remodeled into Sag, SagInfo, Sagevent and SageventInfo


class Sag(RegisteringFraObjekt):
    __tablename__ = "sag"
    # TODO: Sagstype is foreign key
    #    sagstype = Column(String, nullable=False)
    id = Column(String, nullable=False)
    sagsevents = relationship("Sagsevent", order_by="Sagsevent.objectid", backref="sag")
    sagsinfos = relationship("Sagsinfo", order_by="Sagsinfo.objectid", backref="sag")


class Sagsinfo(RegisteringTidObjekt):
    __tablename__ = "sagsinfo"
    objectid = Column(Integer, primary_key=True)
    aktiv = Column(String, nullable=False)
    journalnummer = Column(String)
    behandler = Column(String, nullable=False)
    beskrivelse = Column(String)
    sagid = Column(String, ForeignKey("sag.id"), nullable=False)


class Sagsevent(RegisteringFraObjekt):
    __tablename__ = "sagsevent"
    id = Column(String, nullable=False)
    event = Column(String, nullable=False)
    # beskrivelse = Column(String)
    sagid = Column(String, ForeignKey("sag.id"), nullable=False)
    # TODO: Eventtype, materiale, and rapporthtml
    # Fikspunktregisterobjekter
    punkter = relationship("Punkt", order_by="Punkt.objectid", backref="sagsevent")
    koordinater = relationship(
        "Koordinat", order_by="Koordinat.objectid", backref="sagsevent"
    )
    geometriobjekter = relationship(
        "GeometriObjekt", order_by="GeometriObjekt.objectid", backref="sagsevent"
    )
    observationer = relationship(
        "Observation", order_by="Observation.objectid", backref="sagsevent"
    )
    punktinformationer = relationship(
        "PunktInformation", order_by="PunktInformation.objectid", backref="sagsevent"
    )
    beregninger = relationship(
        "Beregning", order_by="Beregning.objectid", backref="sagsevent"
    )

