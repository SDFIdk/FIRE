import enum
from sqlalchemy import Table, Column, String, Integer, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship

# DeclarativeBase = sqlalchemy.ext.declarative.declarative_base(cls=ReprBase)

from fireapi.model import RegisteringTidObjekt, DeclarativeBase, columntypes

# Eksports
__all__ = [
    "FikspunktregisterObjekt",
    "Punkt",
    "Koordinat",
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
    id = Column(String, nullable=False, unique=True)
    sagseventid = Column(String, ForeignKey("sagsevent.id"), nullable=False)
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
    sagseventid = Column(String(36), ForeignKey("sagsevent.id"), nullable=False)
    sagsevent = relationship("Sagsevent", back_populates="punktinformationer")
    infotype = Column(
        String(4000), ForeignKey("punktinfotype.infotype"), nullable=False
    )
    tal = Column(Float)
    tekst = Column(String(4000))
    punktid = Column(String(36), ForeignKey("punkt.id"), nullable=False)
    punkt = relationship("Punkt", back_populates="punktinformationer")


class PunktInformationType(DeclarativeBase):
    __tablename__ = "punktinfotype"
    objectid = Column(Integer, primary_key=True)
    infotype = Column(String(4000), unique=True, nullable=False)
    anvendelse = Column(Enum(PunktInformationTypeAnvendelse), nullable=False)
    beskrivelse = Column(String(4000), nullable=False)


class Koordinat(FikspunktregisterObjekt):
    __tablename__ = "koordinat"
    _sridid = Column("srid", String, ForeignKey("sridtype.srid"), nullable=False)
    srid = relationship("Srid", back_populates="koordinater")
    sx = Column(Float)
    sy = Column(Float)
    sz = Column(Float)
    t = Column(DateTime(timezone=True))
    transformeret = Column(String, nullable=False)
    x = Column(Float)
    y = Column(Float)
    z = Column(Float)
    sagseventid = Column(String(36), ForeignKey("sagsevent.id"), nullable=False)
    sagsevent = relationship("Sagsevent", back_populates="koordinater")
    punktid = Column(String(36), ForeignKey("punkt.id"), nullable=False)
    punkt = relationship("Punkt", back_populates="koordinater")
    beregninger = relationship(
        "Beregning", secondary=beregning_koordinat, back_populates="koordinater"
    )


class GeometriObjekt(FikspunktregisterObjekt):
    __tablename__ = "geometriobjekt"
    geometri = Column(columntypes.Point(2, 4326), nullable=False)
    sagseventid = Column(String(36), ForeignKey("sagsevent.id"), nullable=False)
    sagsevent = relationship("Sagsevent", back_populates="geometriobjekter")
    punktid = Column(String(36), ForeignKey("punkt.id"), nullable=False)
    punkt = relationship("Punkt", back_populates="geometriobjekter")


class Beregning(FikspunktregisterObjekt):
    __tablename__ = "beregning"
    objectid = Column(Integer, primary_key=True)
    sagseventid = Column(String(36), ForeignKey("sagsevent.id"), nullable=False)
    sagsevent = relationship("Sagsevent", back_populates="beregninger")
    koordinater = relationship(
        "Koordinat", secondary=beregning_koordinat, back_populates="beregninger"
    )
    observationer = relationship(
        "Observation", secondary=beregning_observation, back_populates="beregninger"
    )


class ObservationType(DeclarativeBase):
    __tablename__ = "observationtype"
    objectid = Column(Integer, primary_key=True)
    observationstype = Column(String(4000), nullable=False)
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
    sagseventid = Column(String, ForeignKey("sagsevent.id"), nullable=False)
    sagsevent = relationship("Sagsevent", back_populates="observationer")
    observationstidspunkt = Column(DateTime(timezone=True), nullable=False)
    antal = Column(Integer, nullable=False)
    gruppe = Column(Integer)
    observationstypeid = Column(
        "observationstype", String(4000), ForeignKey("observationtype.observationstype")
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
    srid = Column(String(36), nullable=False, unique=True)
    beskrivelse = Column(String(4000))
    koordinater = relationship("Koordinat", back_populates="srid")
