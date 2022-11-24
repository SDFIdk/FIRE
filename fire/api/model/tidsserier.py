from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from fire.api.model import (
    FikspunktregisterObjekt,
    tidsserie_koordinat,
)

__all__ = [
    "Tidsserie",
    "GNSSTidsserie",
    "HøjdeTidsserie",
]


class TidsserietypeID:
    """
    ID for eksisterende tidsserietyper i FIRE-databasen.

    Notes
    -----
    ID'erne er fastsat i DDL-filerne for databasen og kan derfor fastsættes her.

    """

    gnss = 1
    højde = 2


class Tidsserie(FikspunktregisterObjekt):
    __tablename__ = "tidsserie"
    sagseventfraid = Column(String, ForeignKey("sagsevent.id"), nullable=False)
    sagsevent = relationship(
        "Sagsevent", foreign_keys=[sagseventfraid], back_populates="tidsserier"
    )
    sagseventtilid = Column(String, ForeignKey("sagsevent.id"), nullable=True)
    slettet = relationship(
        "Sagsevent",
        foreign_keys=[sagseventtilid],
        back_populates="tidsserier_slettede",
    )

    punktid = Column(String(36), ForeignKey("punkt.id"))
    punkt = relationship("Punkt")

    punktsamlingsid = Column(Integer, ForeignKey("punktsamling.objektid"))
    punktsamling = relationship("PunktSamling", back_populates="tidsserier")

    navn = Column(String, nullable=False)
    formål = Column("formaal", String, nullable=False)

    referenceramme = Column(String, nullable=False)
    sridid = Column(Integer, ForeignKey("sridtype.sridid"), nullable=False)
    srid = relationship("Srid", lazy="joined")

    tstype = Column(Integer, nullable=False)

    koordinater = relationship(
        "Koordinat", secondary=tidsserie_koordinat, back_populates="tidsserier"
    )

    __mapper_args__ = {
        "polymorphic_identity": "tidsserie",
        "polymorphic_on": tstype,
    }


class GNSSTidsserie(Tidsserie):
    __mapper_args__ = {
        "polymorphic_identity": TidsserietypeID.gnss,
    }


class HøjdeTidsserie(Tidsserie):
    __mapper_args__ = {
        "polymorphic_identity": TidsserietypeID.højde,
    }
