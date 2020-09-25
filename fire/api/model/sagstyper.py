import enum
from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship

import fire
from fire.api.model import (
    RegisteringTidObjekt,
    RegisteringFraObjekt,
    DeclarativeBase,
    IntEnum,
    StringEnum,
    Boolean,
)


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
        "Sagsevent", order_by="Sagsevent.objektid", back_populates="sag"
    )
    sagsinfos = relationship(
        "Sagsinfo", order_by="Sagsinfo.objektid", back_populates="sag"
    )

    @property
    def aktiv(self) -> bool:
        return self.sagsinfos[-1].aktiv == Boolean.TRUE

    @property
    def journalnummer(self) -> str:
        return self.sagsinfos[-1].journalnummer

    @property
    def behandler(self) -> str:
        return self.sagsinfos[-1].behandler

    @property
    def beskrivelse(self) -> str:
        if self.sagsinfos[-1].beskrivelse is None:
            return ""
        return self.sagsinfos[-1].beskrivelse


class Sagsinfo(RegisteringTidObjekt):
    __tablename__ = "sagsinfo"
    aktiv = Column(StringEnum(Boolean), nullable=False, default=Boolean.TRUE)
    journalnummer = Column(String)
    behandler = Column(String, nullable=False)
    beskrivelse = Column(String)
    sagsid = Column(String, ForeignKey("sag.id"), nullable=False)
    sag = relationship("Sag", back_populates="sagsinfos")


class Sagsevent(RegisteringFraObjekt):
    __tablename__ = "sagsevent"
    id = Column(String(36), nullable=False, default=fire.uuid)
    eventtype = Column("eventtypeid", IntEnum(EventType), nullable=False)
    sagsid = Column(String(36), ForeignKey("sag.id"), nullable=False)
    sag = relationship("Sag", back_populates="sagsevents")
    sagseventinfos = relationship(
        "SagseventInfo", order_by="SagseventInfo.objektid", back_populates="sagsevent"
    )
    # Fikspunktregisterobjekter
    punkter = relationship(
        "Punkt",
        order_by="Punkt.objektid",
        back_populates="sagsevent",
        foreign_keys="Punkt.sagseventfraid",
    )
    punkter_slettede = relationship(
        "Punkt",
        order_by="Punkt.objektid",
        back_populates="slettet",
        foreign_keys="Punkt.sagseventtilid",
    )
    koordinater = relationship(
        "Koordinat",
        order_by="Koordinat.objektid",
        back_populates="sagsevent",
        foreign_keys="Koordinat.sagseventfraid",
    )
    koordinater_slettede = relationship(
        "Koordinat",
        order_by="Koordinat.objektid",
        back_populates="slettet",
        foreign_keys="Koordinat.sagseventtilid",
    )
    geometriobjekter = relationship(
        "GeometriObjekt",
        order_by="GeometriObjekt.objektid",
        back_populates="sagsevent",
        foreign_keys="GeometriObjekt.sagseventfraid",
    )
    geometriobjekter_slettede = relationship(
        "GeometriObjekt",
        order_by="GeometriObjekt.objektid",
        back_populates="slettet",
        foreign_keys="GeometriObjekt.sagseventtilid",
    )
    observationer = relationship(
        "Observation",
        order_by="Observation.objektid",
        back_populates="sagsevent",
        foreign_keys="Observation.sagseventfraid",
    )
    observationer_slettede = relationship(
        "Observation",
        order_by="Observation.objektid",
        back_populates="slettet",
        foreign_keys="Observation.sagseventtilid",
    )
    punktinformationer = relationship(
        "PunktInformation",
        order_by="PunktInformation.objektid",
        back_populates="sagsevent",
        foreign_keys="PunktInformation.sagseventfraid",
    )
    punktinformationer_slettede = relationship(
        "PunktInformation",
        order_by="PunktInformation.objektid",
        back_populates="slettet",
        foreign_keys="PunktInformation.sagseventtilid",
    )
    beregninger = relationship(
        "Beregning",
        order_by="Beregning.objektid",
        back_populates="sagsevent",
        foreign_keys="Beregning.sagseventfraid",
    )
    beregninger_slettede = relationship(
        "Beregning",
        order_by="Beregning.objektid",
        back_populates="slettet",
        foreign_keys="Beregning.sagseventtilid",
    )

    @property
    def beskrivelse(self) -> str:
        if self.sagseventinfos[-1].beskrivelse is None:
            return ""
        return self.sagseventinfos[-1].beskrivelse


class SagseventInfo(RegisteringTidObjekt):
    __tablename__ = "sagseventinfo"
    beskrivelse = Column(String(4000))
    sagseventid = Column(String(36), ForeignKey("sagsevent.id"), nullable=False)
    sagsevent = relationship("Sagsevent", back_populates="sagseventinfos")
    materialer = relationship(
        "SagseventInfoMateriale",
        order_by="SagseventInfoMateriale.objektid",
        back_populates="sagseventinfo",
    )
    htmler = relationship(
        "SagseventInfoHtml",
        order_by="SagseventInfoHtml.objektid",
        back_populates="sagseventinfo",
    )


class SagseventInfoMateriale(DeclarativeBase):
    __tablename__ = "sagseventinfo_materiale"
    objektid = Column(Integer, primary_key=True)
    md5sum = Column(String(32), nullable=False)
    sti = Column(String(4000), nullable=False)
    sagseventinfoobjektid = Column(
        Integer, ForeignKey("sagseventinfo.objektid"), nullable=False
    )
    sagseventinfo = relationship("SagseventInfo", back_populates="materialer")


class SagseventInfoHtml(DeclarativeBase):
    __tablename__ = "sagseventinfo_html"
    objektid = Column(Integer, primary_key=True)
    html = Column(String, nullable=False)
    sagseventinfoobjektid = Column(
        Integer, ForeignKey("sagseventinfo.objektid"), nullable=False
    )
    sagseventinfo = relationship("SagseventInfo", back_populates="htmler")
