import enum
from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship

import fire
from fire.api.model import (
    RegisteringTidObjekt,
    RegisteringFraObjekt,
    DeclarativeBase,
)
from fire.api.model.columntypes import IntegerEnum


# Model this as a hard coded enum for now. This makes it a lot easier for the user. It would be nice to sync this with
# the db table eventtype
class EventType(enum.Enum):
    KOORDINAT_BEREGNET = 1
    KOORDINAT_NEDLAGT = 2
    OBSERVATION_INDSAT = 3
    OBSERVATION_NEDLAGT = 4
    PUNKTINFO_TILFOEJET = 5
    PUNKTINFO_FJERNET = 6
    PUNKT_OPRETTET = 7
    PUNKT_NEDLAGT = 8
    KOMMENTAR = 9


class Sag(RegisteringFraObjekt):
    __tablename__ = "sag"
    id = Column(String(36), nullable=False, default=fire.uuid)
    sagsevents = relationship(
        "Sagsevent", order_by="Sagsevent.objectid", back_populates="sag"
    )
    sagsinfos = relationship(
        "Sagsinfo", order_by="Sagsinfo.objectid", back_populates="sag"
    )

    @property
    def aktiv(self) -> bool:
        return self.sagsinfos[-1].aktiv != "false"


class Sagsinfo(RegisteringTidObjekt):
    __tablename__ = "sagsinfo"
    aktiv = Column(String(5), nullable=False)
    journalnummer = Column(String)
    behandler = Column(String, nullable=False)
    beskrivelse = Column(String)
    sagid = Column(String, ForeignKey("sag.id"), nullable=False)
    sag = relationship("Sag", back_populates="sagsinfos")


class Sagsevent(RegisteringFraObjekt):
    __tablename__ = "sagsevent"
    id = Column(String(36), nullable=False, default=fire.uuid)
    eventtype = Column("eventtypeid", IntegerEnum(EventType), nullable=False)
    sagid = Column(String(36), ForeignKey("sag.id"), nullable=False)
    sag = relationship("Sag", back_populates="sagsevents")
    sagseventinfos = relationship(
        "SagseventInfo", order_by="SagseventInfo.objectid", back_populates="sagsevent"
    )
    # Fikspunktregisterobjekter
    punkter = relationship(
        "Punkt",
        order_by="Punkt.objectid",
        back_populates="sagsevent",
        foreign_keys="Punkt.sagseventfraid",
    )
    punkter_slettede = relationship(
        "Punkt",
        order_by="Punkt.objectid",
        back_populates="slettet",
        foreign_keys="Punkt.sagseventtilid",
    )
    koordinater = relationship(
        "Koordinat",
        order_by="Koordinat.objectid",
        back_populates="sagsevent",
        foreign_keys="Koordinat.sagseventfraid",
    )
    koordinater_slettede = relationship(
        "Koordinat",
        order_by="Koordinat.objectid",
        back_populates="slettet",
        foreign_keys="Koordinat.sagseventtilid",
    )
    geometriobjekter = relationship(
        "GeometriObjekt",
        order_by="GeometriObjekt.objectid",
        back_populates="sagsevent",
        foreign_keys="GeometriObjekt.sagseventfraid",
    )
    geometriobjekter_slettede = relationship(
        "GeometriObjekt",
        order_by="GeometriObjekt.objectid",
        back_populates="slettet",
        foreign_keys="GeometriObjekt.sagseventtilid",
    )
    observationer = relationship(
        "Observation",
        order_by="Observation.objectid",
        back_populates="sagsevent",
        foreign_keys="Observation.sagseventfraid",
    )
    observationer_slettede = relationship(
        "Observation",
        order_by="Observation.objectid",
        back_populates="slettet",
        foreign_keys="Observation.sagseventtilid",
    )
    punktinformationer = relationship(
        "PunktInformation",
        order_by="PunktInformation.objectid",
        back_populates="sagsevent",
        foreign_keys="PunktInformation.sagseventfraid",
    )
    punktinformationer_slettede = relationship(
        "PunktInformation",
        order_by="PunktInformation.objectid",
        back_populates="slettet",
        foreign_keys="PunktInformation.sagseventtilid",
    )
    beregninger = relationship(
        "Beregning",
        order_by="Beregning.objectid",
        back_populates="sagsevent",
        foreign_keys="Beregning.sagseventfraid",
    )
    beregninger_slettede = relationship(
        "Beregning",
        order_by="Beregning.objectid",
        back_populates="slettet",
        foreign_keys="Beregning.sagseventtilid",
    )


class SagseventInfo(RegisteringTidObjekt):
    __tablename__ = "sagseventinfo"
    beskrivelse = Column(String(4000))
    sagseventid = Column(String(36), ForeignKey("sagsevent.id"), nullable=False)
    sagsevent = relationship("Sagsevent", back_populates="sagseventinfos")
    materialer = relationship(
        "SagseventInfoMateriale",
        order_by="SagseventInfoMateriale.objectid",
        back_populates="sagseventinfo",
    )
    htmler = relationship(
        "SagseventInfoHtml",
        order_by="SagseventInfoHtml.objectid",
        back_populates="sagseventinfo",
    )


class SagseventInfoMateriale(DeclarativeBase):
    __tablename__ = "sagseventinfo_materiale"
    objectid = Column(Integer, primary_key=True)
    md5sum = Column(String(32), nullable=False)
    sti = Column(String(4000), nullable=False)
    sagseventinfoobjectid = Column(
        Integer, ForeignKey("sagseventinfo.objectid"), nullable=False
    )
    sagseventinfo = relationship("SagseventInfo", back_populates="materialer")


class SagseventInfoHtml(DeclarativeBase):
    __tablename__ = "sagseventinfo_html"
    objectid = Column(Integer, primary_key=True)
    html = Column(String, nullable=False)
    sagseventinfoobjectid = Column(
        Integer, ForeignKey("sagseventinfo.objectid"), nullable=False
    )
    sagseventinfo = relationship("SagseventInfo", back_populates="htmler")
