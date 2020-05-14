import enum
from sqlalchemy import Table, Column, String, Integer, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship

# DeclarativeBase = sqlalchemy.ext.declarative.declarative_base(cls=ReprBase)

import fire
from fire.api.model import (
    IntEnum,
    RegisteringTidObjekt,
    DeclarativeBase,
    columntypes,
)

# Eksports
__all__ = [
    "FikspunktregisterObjekt",
    "Punkt",
    "Koordinat",
    "Artskode",
    "GeometriObjekt",
    "Beregning",
    "ObservationType",
    "Observation",
    "PunktInformation",
    "PunktInformationType",
    "PunktInformationTypeAnvendelse",
    "Srid",
]


class PunktInformationTypeAnvendelse(enum.Enum):
    FLAG = "FLAG"
    TAL = "TAL"
    TEKST = "TEKST"


class Artskode(enum.Enum):
    """
    Uddybende beskrivelser fra REFGEO:

    artskode = 1 control point in fundamental network, first order.
    artskode = 2 control point in superior plane network.
    artskode = 2 control point in superior height network.
    artskode = 3 control point in network of high quality.
    artskode = 4 control point in network of lower or unknown quality.
    artskode = 5 coordinate computed on just a few measurements.
    artskode = 6 coordinate transformed from local or an not valid coordinate system.
    artskode = 7 coordinate computed on an not valid coordinate system, or system of
                 unknown origin.
    artskode = 8 coordinate computed on few measurements, and on an not valid
                 coordinate system.
    artskode = 9 location coordinate or location height.
    """

    FUNDAMENTAL_PUNKT = 1
    NETVAERK_AF_GOD_KVALITET = 2
    NETVAERK_AF_HOEJ_KVALITET = 3
    NETVAERK_AF_LAV_KVALITET = 4
    BESTEMT_FRA_FAA_OBSERVATIONER = 5
    TRANSFORMERET = 6
    UKENDT_KOORDINATSYSTEM = 7
    FAA_OBS_OG_UKENDT_KOORDINATSYSTEM = 8
    LOKATIONSKOORDINAT = 9
    NULL = None


beregning_koordinat = Table(
    "beregning_koordinat",
    DeclarativeBase.metadata,
    Column("beregningobjectid", Integer, ForeignKey("beregning.objectid")),
    Column("koordinatobjectid", Integer, ForeignKey("koordinat.objectid")),
)


beregning_observation = Table(
    "beregning_observation",
    DeclarativeBase.metadata,
    Column("beregningobjectid", Integer, ForeignKey("beregning.objectid")),
    Column("observationobjectid", Integer, ForeignKey("observation.objectid")),
)


class FikspunktregisterObjekt(RegisteringTidObjekt):
    __abstract__ = True


class Punkt(FikspunktregisterObjekt):
    __tablename__ = "punkt"
    id = Column(String, nullable=False, unique=True, default=fire.uuid)
    sagseventfraid = Column(String, ForeignKey("sagsevent.id"), nullable=False)
    sagsevent = relationship(
        "Sagsevent", foreign_keys=[sagseventfraid], back_populates="punkter"
    )
    sagseventtilid = Column(String, ForeignKey("sagsevent.id"), nullable=True)
    slettet = relationship(
        "Sagsevent", foreign_keys=[sagseventtilid], back_populates="punkter_slettede"
    )
    koordinater = relationship(
        "Koordinat", order_by="Koordinat.objectid", back_populates="punkt"
    )
    geometriobjekter = relationship(
        "GeometriObjekt", order_by="GeometriObjekt.objectid", back_populates="punkt"
    )
    punktinformationer = relationship(
        "PunktInformation", order_by="PunktInformation.objectid", back_populates="punkt"
    )
    observationer_fra = relationship(
        "Observation",
        order_by="Observation.opstillingspunktid",
        back_populates="opstillingspunkt",
        foreign_keys="Observation.opstillingspunktid",
    )
    observationer_til = relationship(
        "Observation",
        order_by="Observation.sigtepunktid",
        back_populates="sigtepunkt",
        foreign_keys="Observation.sigtepunktid",
    )


class PunktInformation(FikspunktregisterObjekt):
    __tablename__ = "punktinfo"
    sagseventfraid = Column(String, ForeignKey("sagsevent.id"), nullable=False)
    sagsevent = relationship(
        "Sagsevent", foreign_keys=[sagseventfraid], back_populates="punktinformationer"
    )
    sagseventtilid = Column(String, ForeignKey("sagsevent.id"), nullable=True)
    slettet = relationship(
        "Sagsevent",
        foreign_keys=[sagseventtilid],
        back_populates="punktinformationer_slettede",
    )
    infotypeid = Column(Integer, ForeignKey("punktinfotype.infotypeid"), nullable=False)
    infotype = relationship("PunktInformationType")
    tal = Column(Float)
    tekst = Column(String(4000))
    punktid = Column(String(36), ForeignKey("punkt.id"), nullable=False)
    punkt = relationship("Punkt", back_populates="punktinformationer")


class PunktInformationType(DeclarativeBase):
    __tablename__ = "punktinfotype"
    objectid = Column(Integer, primary_key=True)
    infotypeid = Column(Integer, unique=True, nullable=False)
    name = Column("infotype", String(4000), nullable=False)
    anvendelse = Column(Enum(PunktInformationTypeAnvendelse), nullable=False)
    beskrivelse = Column(String(4000), nullable=False)


class Koordinat(FikspunktregisterObjekt):
    __tablename__ = "koordinat"
    sridid = Column(Integer, ForeignKey("sridtype.sridid"), nullable=False)
    srid = relationship("Srid")
    sx = Column(Float)
    sy = Column(Float)
    sz = Column(Float)
    t = Column(DateTime(timezone=True))
    transformeret = Column(String, nullable=False, default="false")
    artskode = Column(IntEnum(Artskode), nullable=True, default=Artskode.NULL)
    x = Column(Float)
    y = Column(Float)
    z = Column(Float)
    sagseventfraid = Column(String, ForeignKey("sagsevent.id"), nullable=False)
    sagsevent = relationship(
        "Sagsevent", foreign_keys=[sagseventfraid], back_populates="koordinater"
    )
    sagseventtilid = Column(String, ForeignKey("sagsevent.id"), nullable=True)
    slettet = relationship(
        "Sagsevent",
        foreign_keys=[sagseventtilid],
        back_populates="koordinater_slettede",
    )
    punktid = Column(String(36), ForeignKey("punkt.id"), nullable=False)
    punkt = relationship("Punkt", back_populates="koordinater")
    beregninger = relationship(
        "Beregning", secondary=beregning_koordinat, back_populates="koordinater"
    )


class GeometriObjekt(FikspunktregisterObjekt):
    __tablename__ = "geometriobjekt"
    geometri = Column(columntypes.Point(2, 4326), nullable=False)
    sagseventfraid = Column(String, ForeignKey("sagsevent.id"), nullable=False)
    sagsevent = relationship(
        "Sagsevent", foreign_keys=[sagseventfraid], back_populates="geometriobjekter"
    )
    sagseventtilid = Column(String, ForeignKey("sagsevent.id"), nullable=True)
    slettet = relationship(
        "Sagsevent",
        foreign_keys=[sagseventtilid],
        back_populates="geometriobjekter_slettede",
    )
    punktid = Column(String(36), ForeignKey("punkt.id"), nullable=False)
    punkt = relationship("Punkt", back_populates="geometriobjekter")


class Beregning(FikspunktregisterObjekt):
    __tablename__ = "beregning"
    objectid = Column(Integer, primary_key=True)
    sagseventfraid = Column(String, ForeignKey("sagsevent.id"), nullable=False)
    sagsevent = relationship(
        "Sagsevent", foreign_keys=[sagseventfraid], back_populates="beregninger"
    )
    sagseventtilid = Column(String, ForeignKey("sagsevent.id"), nullable=True)
    slettet = relationship(
        "Sagsevent",
        foreign_keys=[sagseventtilid],
        back_populates="beregninger_slettede",
    )
    koordinater = relationship(
        "Koordinat", secondary=beregning_koordinat, back_populates="beregninger"
    )
    observationer = relationship(
        "Observation", secondary=beregning_observation, back_populates="beregninger"
    )


class ObservationType(DeclarativeBase):
    __tablename__ = "observationtype"
    objectid = Column(Integer, primary_key=True)
    observationstypeid = Column(Integer, unique=True, nullable=False)
    name = Column("observationstype", String(4000), nullable=False)
    beskrivelse = Column(String(4000), nullable=False)
    value1 = Column(String, nullable=False)
    value2 = Column(String)
    value3 = Column(String)
    value4 = Column(String)
    value5 = Column(String)
    value6 = Column(String)
    value7 = Column(String)
    value8 = Column(String)
    value9 = Column(String)
    value10 = Column(String)
    value11 = Column(String)
    value12 = Column(String)
    value13 = Column(String)
    value14 = Column(String)
    value15 = Column(String)
    sigtepunkt = Column(String(5), nullable=False)
    observationer = relationship(
        "Observation",
        order_by="Observation.objectid",
        back_populates="observationstype",
    )


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
    sagseventfraid = Column(String, ForeignKey("sagsevent.id"), nullable=False)
    sagsevent = relationship(
        "Sagsevent", foreign_keys=[sagseventfraid], back_populates="observationer"
    )
    sagseventtilid = Column(String, ForeignKey("sagsevent.id"), nullable=True)
    slettet = relationship(
        "Sagsevent",
        foreign_keys=[sagseventtilid],
        back_populates="observationer_slettede",
    )
    observationstidspunkt = Column(DateTime(timezone=True), nullable=False)
    antal = Column(Integer, nullable=False, default=1)
    gruppe = Column(Integer)
    observationstypeid = Column(
        Integer, ForeignKey("observationtype.observationstypeid")
    )
    observationstype = relationship("ObservationType", back_populates="observationer")
    sigtepunktid = Column(String(36), ForeignKey("punkt.id"))
    sigtepunkt = relationship("Punkt", foreign_keys=[sigtepunktid])
    opstillingspunktid = Column(String(36), ForeignKey("punkt.id"))
    opstillingspunkt = relationship("Punkt", foreign_keys=[opstillingspunktid])
    beregninger = relationship(
        "Beregning", secondary=beregning_observation, back_populates="observationer"
    )


class Srid(DeclarativeBase):
    __tablename__ = "sridtype"
    objectid = Column(Integer, primary_key=True)
    sridid = Column(Integer, unique=True, nullable=False)
    name = Column("srid", String(36), nullable=False, unique=True)
    beskrivelse = Column(String(4000))
    x = Column(String(4000))
    y = Column(String(4000))
    z = Column(String(4000))
