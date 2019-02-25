import enum
from sqlalchemy import Column, String, Integer, ForeignKey, Enum
from sqlalchemy.orm import relationship

from fireapi.model import RegisteringTidObjekt, RegisteringFraObjekt, DeclarativeBase


# Model this as a hard coded enum for now. This makes it a lot easier for the user. It would be nice to sync this with
# the db table eventtype
class EventType(enum.Enum):
    KOORDINAT_BEREGNET = "koordinat_beregnet"
    KOORDINAT_NEDLAGT = "koordinat_nedlagt"
    OBSERVATION_INDSAT = "observation_indsat"
    OBSERVATION_NEDLAGT = "observation_nedlagt"
    PUNKTINFO_TILFOEJET = "punktinfo_tilføjet"
    PUNKTINFO_FJERNET = "punktinfo_fjernet"
    PUNKT_OPRETTET = "punkt_oprettet"
    PUNKT_NEDLAGT = "punkt_nedlagt"
    BEREGNING = "beregning"
    KOMMENTAR = "kommentar"


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
    aktiv = Column(String(5), nullable=False)
    journalnummer = Column(String)
    behandler = Column(String, nullable=False)
    beskrivelse = Column(String)
    sagid = Column(String, ForeignKey("sag.id"), nullable=False)
    sag = relationship("Sag", back_populates="sagsinfos")


class Sagsevent(RegisteringFraObjekt):
    __tablename__ = "sagsevent"
    id = Column(String(36), nullable=False)
    event = Column(Enum(EventType), nullable=False)
    # beskrivelse = Column(String)
    sagid = Column(String(36), ForeignKey("sag.id"), nullable=False)
    sag = relationship("Sag", back_populates="sagsevents")
    sagseventinfos = relationship(
        "SagseventInfo", order_by="SagseventInfo.objectid", back_populates="sagsevent"
    )
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
