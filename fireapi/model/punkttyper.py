from sqlalchemy import Table, Column, String, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship

# DeclarativeBase = sqlalchemy.ext.declarative.declarative_base(cls=ReprBase)

from . import RegisteringTidObjekt, DeclarativeBase, columntypes

# Eksports
__all__ = [
    "FikspunktregisterObjekt",
    "Punkt",
    "Koordinat",
    "GeometriObjekt",
    "Beregning",
    "ObservationType",
    "Observation",
]


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
    koordinater = relationship(
        "Koordinat", order_by="Koordinat.objectid", backref="punkt"
    )
    geometriobjekter = relationship(
        "GeometriObjekt", order_by="GeometriObjekt.objectid", backref="punkt"
    )
    punktinformationer = relationship(
        "PunktInformation", order_by="PunktInformation.objectid", backref="punkt"
    )
    # TODO: Observationer (Note Observation has three references to Punkt. How to handle this?)
    # Maybe use: "observationer_til" referencing Observation.Sigtepunkt and "observationer_fra" referencing Observation.opstillingspunkt


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
    sagseventid = Column(String, ForeignKey("sagsevent.id"), nullable=False)
    punktid = Column(String, ForeignKey("punkt.id"), nullable=False)
    beregninger = relationship(
        "Beregning", secondary=beregning_koordinat, back_populates="koordinater"
    )


class GeometriObjekt(FikspunktregisterObjekt):
    __tablename__ = "geometriobjekt"
    geometri = Column(columntypes.Point(2, 4326), nullable=False)
    sagseventid = Column(String, ForeignKey("sagsevent.id"), nullable=False)
    punktid = Column(String, ForeignKey("punkt.id"), nullable=False)


class Beregning(FikspunktregisterObjekt):
    __tablename__ = "beregning"
    objectid = Column(Integer, primary_key=True)
    sagseventid = Column(String, ForeignKey("sagsevent.id"), nullable=False)
    koordinater = relationship(
        "Koordinat", secondary=beregning_koordinat, back_populates="beregninger"
    )
    observationer = relationship(
        "Observation", secondary=beregning_observation, back_populates="beregninger"
    )


class ObservationType(DeclarativeBase):
    __tablename__ = "observationtype"
    objectid = Column(Integer, primary_key=True)
    observationstype = Column(String, nullable=False)
    beskrivelse = Column(String, nullable=False)
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
    sigtepunkt = Column(String, nullable=False)
    observationer = relationship(
        "Observation", order_by="Observation.objectid", backref="observationstype"
    )


class Observation(FikspunktregisterObjekt):
    __tablename__ = "observation"
    objectid = Column(Integer, primary_key=True)
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
    observationstidspunkt = Column(DateTime(timezone=True), nullable=False)
    antal = Column(Integer, nullable=False)
    gruppe = Column(Integer)
    observationstypeid = Column(
        "observationstype", String, ForeignKey("observationtype.observationstype")
    )
    sigtepunktid = Column(String, ForeignKey("punkt.id"))
    sigtepunkt = relationship("Punkt", foreign_keys=[sigtepunktid])
    opstillingspunktid = Column(String, ForeignKey("punkt.id"))
    opstillingspunkt = relationship("Punkt", foreign_keys=[opstillingspunktid])
    beregninger = relationship(
        "Beregning", secondary=beregning_observation, back_populates="observationer"
    )


class PunktInformation(FikspunktregisterObjekt):
    __tablename__ = "punktinfo"
    sagseventid = Column(String, ForeignKey("sagsevent.id"), nullable=False)
    # TODO: Infotype is foreign key
    infotype = Column(String, nullable=False)
    reeltal = Column(Float)
    tekst = Column(String)
    punktid = Column(String, ForeignKey("punkt.id"), nullable=False)
