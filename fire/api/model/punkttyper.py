from __future__ import annotations
import enum
from typing import List, Union
import functools

from sqlalchemy import (
    Table,
    Column,
    String,
    Integer,
    Float,
    ForeignKey,
    Enum,
    func,
)
from sqlalchemy.orm import relationship, reconstructor
from sqlalchemy.dialects.oracle import TIMESTAMP
from sqlalchemy.ext.declarative import declared_attr

import fire
from fire.api.model import (
    IntEnum,
    StringEnum,
    RegisteringTidObjekt,
    DeclarativeBase,
    columntypes,
)

__all__ = [
    "FikspunktregisterObjekt",
    "Punkt",
    "Koordinat",
    "Artskode",
    "GeometriObjekt",
    "Beregning",
    "ObservationsType",
    "Observation",
    "GeometriskKoteforskel",
    "TrigonometriskKoteforskel",
    "PunktInformation",
    "PunktInformationType",
    "PunktInformationTypeAnvendelse",
    "Srid",
    "Boolean",
    "Ident",
    "FikspunktsType",
]


class PunktInformationTypeAnvendelse(enum.Enum):
    FLAG = "FLAG"
    TAL = "TAL"
    TEKST = "TEKST"


class Boolean(enum.Enum):
    TRUE = "true"
    FALSE = "false"


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
    artskode = 7 coordinate computed on an not valid coordinate system, or system of unknown origin.
    artskode = 8 coordinate computed on few measurements, and on an not valid coordinate system.
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


class FikspunktsType(enum.Enum):

    GI = 1
    MV = 2
    HØJDE = 3
    JESSEN = 4
    HJÆLPEPUNKT = 5
    VANDSTANDSBRÆT = 6


beregning_koordinat = Table(
    "beregning_koordinat",
    DeclarativeBase.metadata,
    Column("beregningobjektid", Integer, ForeignKey("beregning.objektid")),
    Column("koordinatobjektid", Integer, ForeignKey("koordinat.objektid")),
)


beregning_observation = Table(
    "beregning_observation",
    DeclarativeBase.metadata,
    Column("beregningobjektid", Integer, ForeignKey("beregning.objektid")),
    Column("observationobjektid", Integer, ForeignKey("observation.objektid")),
)


class FikspunktregisterObjekt(RegisteringTidObjekt):
    __abstract__ = True


@functools.total_ordering
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
        "Koordinat", order_by="Koordinat.objektid", back_populates="punkt"
    )
    geometriobjekter = relationship(
        "GeometriObjekt",
        order_by="GeometriObjekt.objektid",
        back_populates="punkt",
    )
    punktinformationer = relationship(
        "PunktInformation",
        order_by="PunktInformation.objektid",
        back_populates="punkt",
        lazy="joined",
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

    @reconstructor
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._identer = []

    def _populer_identer(self):
        """
        Skab liste med ident-punktinformationer tilhørende punktet.
        """
        if not self._identer:
            temp = []
            for punktinfo in self.punktinformationer:
                if punktinfo.registreringtil:
                    continue
                if punktinfo.infotype.name.startswith("IDENT:") and punktinfo.tekst:
                    temp.append(Ident(punktinfo))

            # Tilføj kort uuid som bagstopper-ident
            if self.id:
                temp.append(Ident(self.id[0:8]))

            self._identer = sorted(temp)

    @property
    def geometri(self):
        try:
            return self.geometriobjekter[-1]
        except IndexError:
            return None

    @property
    def identer(self) -> List[str]:
        """
        Returner liste over alle identer der er tilknyttet Punktet
        """
        self._populer_identer()
        if self._identer:
            return [str(ident) for ident in self._identer if ident]
        return []

    @property
    def ident(self) -> str:
        """
        Udtræk det geodætisk mest læsbare ident.

        I nævnte rækkefølge:
            - IDENT:GI
            - IDENT:GNSS,
            - IDENT:landsr
            - IDENT:jessen
            - IDENT:station
            - IDENT:ekstern
            - IDENT:diverse
            - IDENT:refgeo_id.

        Hvis et punkt overhovedet ikke har noget ident returneres uuiden
        uforandret.
        """
        self._populer_identer()

        try:
            return str(self._identer[0])
        except (IndexError, TypeError):
            if self.id:
                return self.id[0:8]
            else:
                return None

    @property
    def tabtgået(self) -> bool:
        for punktinfo in self.punktinformationer:
            if punktinfo.infotype.name == "ATTR:tabtgået":
                return True
        return False

    @property
    def landsnummer(self) -> str:
        landsnumre = []
        for punktinfo in self.punktinformationer:
            if (
                punktinfo.infotype.name == "IDENT:landsnr"
                and not punktinfo.registreringtil
            ):
                landsnumre.append(punktinfo.tekst)

        if landsnumre:
            return sorted(landsnumre)[0]

        return self.ident

    def __lt__(self, other: Punkt) -> bool:
        return self.landsnummer < other.landsnummer

    def __eq__(self, other: Punkt) -> bool:
        return self.landsnummer == other.landsnummer

    def __hash__(self) -> int:
        return hash(self.id)


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
    infotype = relationship("PunktInformationType", lazy="joined")
    tal = Column(Float)
    tekst = Column(String(4000))
    punktid = Column(String(36), ForeignKey("punkt.id"), nullable=False)
    punkt = relationship("Punkt", back_populates="punktinformationer")


@functools.total_ordering
class Ident:
    class IdentType(enum.Enum):
        GI = 1
        GNSS = 2
        LANDSNR = 3
        JESSEN = 4
        STATION = 5
        EKSTERN = 6
        DIVERSE = 7
        REFGEO = 8
        UKENDT = 9
        KORTUUID = 10

    def __init__(self, punktinfo: Union[PunktInformation, str]):
        if isinstance(punktinfo, PunktInformation):
            if not punktinfo.infotype.name.startswith("IDENT:"):
                raise ValueError("punktinfo indeholder ikke en ident")

            self.variant = punktinfo.infotype.name
            self.tekst = punktinfo.tekst
        else:
            # Vi antager der er spyttet et kort uuid ind
            self.variant = "kortuuid"
            self.tekst = punktinfo

    def __lt__(self, other: Ident):
        """
        Bruges til at sortere identer med sorted().

        IdentType definerer rangordenen blandt de forskellige typer identer.
        """
        # jo lavere værdi, des bedre ident
        if self._type.value == other._type.value:
            # hvis samme type, sammenligner vi på selve identen istedet
            if self.tekst < other.tekst:
                return True
            else:
                return False

        if self._type.value < other._type.value:
            return True
        else:
            return False

    def __eq__(self, other: Ident):
        return self.tekst == str(other)

    def __str__(self):
        return self.tekst

    def __repr__(self):
        return f"{self.__class__.__name__}<{self.variant}: {self.tekst}>"

    @property
    def _type(self) -> IdentType:
        if self.variant == "IDENT:GI":
            return self.IdentType.GI
        if self.variant == "IDENT:GNSS":
            return self.IdentType.GNSS
        if self.variant == "IDENT:landsnr":
            return self.IdentType.LANDSNR
        if self.variant == "IDENT:jessen":
            return self.IdentType.JESSEN
        if self.variant == "IDENT:station":
            return self.IdentType.STATION
        if self.variant == "IDENT:ekstern":
            return self.IdentType.EKSTERN
        if self.variant == "IDENT:diverse":
            return self.IdentType.DIVERSE
        if self.variant == "IDENT:refgeo_id":
            return self.IdentType.REFGEO
        if self.variant == "kortuuid":
            return self.IdentType.KORTUUID

        return self.IdentType.UKENDT


class PunktInformationType(DeclarativeBase):
    __tablename__ = "punktinfotype"
    objektid = Column(Integer, primary_key=True)
    infotypeid = Column(Integer, unique=True, nullable=False)
    name = Column("infotype", String(4000), nullable=False)
    anvendelse = Column(Enum(PunktInformationTypeAnvendelse), nullable=False)
    beskrivelse = Column(String(4000), nullable=False)


class Koordinat(FikspunktregisterObjekt):
    __tablename__ = "koordinat"
    sridid = Column(Integer, ForeignKey("sridtype.sridid"), nullable=False)
    srid = relationship("Srid", lazy="joined")
    sx = Column(Float)
    sy = Column(Float)
    sz = Column(Float)
    t = Column(TIMESTAMP(timezone=True), default=func.current_timestamp())
    transformeret = Column(StringEnum(Boolean), nullable=False, default=Boolean.FALSE)
    _fejlmeldt = Column(
        "fejlmeldt", StringEnum(Boolean), nullable=False, default=Boolean.FALSE
    )
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

    @property
    def fejlmeldt(self):
        return self._fejlmeldt == Boolean.TRUE

    @fejlmeldt.setter
    def fejlmeldt(self, value: Boolean):
        if value:
            self._fejlmeldt = Boolean.TRUE
        else:
            self._fejlmeldt = Boolean.FALSE


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

    @property
    def koordinater(self):
        return self.geometri.__geo_interface__["coordinates"]


class Beregning(FikspunktregisterObjekt):
    __tablename__ = "beregning"
    objektid = Column(Integer, primary_key=True)
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


class ObservationsType(DeclarativeBase):
    __tablename__ = "observationstype"
    objektid = Column(Integer, primary_key=True)
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
    sigtepunkt = Column(StringEnum(Boolean), nullable=False, default=Boolean.FALSE)
    observationer = relationship(
        "Observation",
        order_by="Observation.objektid",
        back_populates="observationstype",
    )


class ObservationstypeID:
    """
    ID for eksisterende observationstyper i FIREDB-databasen.

    Notes
    -----
    ID'erne er fastsat i DDL-filerne for databasen og kan derfor fastsættes her.

    """

    geometrisk_koteforskel = 1
    trigonometrisk_koteforskel = 2
    retning = 3
    horisontalafstand = 4
    skråafstand = 5
    zenitvinkel = 6
    vektor = 7
    nulobservation = 8


# Her bruger vi SQLAlchemy's Single Inheritance-funktionalitet:
#
# En instans af `Observation` har kolonnerne `value1..15`, hvor indholdets betydning
# er defineret af observationstypen givet ved informationerne i entiteten `Observationstype`.
#
# Med ovennævnte funktionalitet kan man nedarve fra en entitet, her `Observation`, og angive
# meningsfulde navne for de pågældende kolonner. Ved hjælp af `__mapper_args__`-indgangene
# `polymorphic_on` og `polymorphic_identity` kan man skelne mellem observationstyperne med hver
# sin observationsklasse---eksempelvis `GeometriskKoteforskel`, når `polymorphic_identity`
# er 1, da 1 er det faste ID i `ObservationstypeID`, der angiver en geometrisk koteforskel.
#
# Endelig løsning, erfaringer og rationale:
#
# Med kun én nedarvning (observationsklasse), eksempelvis `GeometriskKoteforskel`,
# fungerer nedarvningen fint. Man kan lave en simpel mapping med en linie som
# følgende i den nedarvede klasse:
#
#     class GeometriskKoteforskel(Observation):
#         __mapper_args__ = {
#             "polymorphic_identity": ObservationstypeID.geometrisk_koteforskel,
#         }
#
#         koteforskel = Column('value1', Float, nullable=False)
#         "Koteforskel / [m]"
#
#         nivlængde = Column('value2', Float)
#         "Nivellementslængde / [m]"
#
#         (...)
#
# Men med to eller flere nedarvninger af `Observation`, e.g med klassen
# `TrigonometriskKoteforskel`, kommer der sammenstød mellem attribut-navnene.
#
# Ifølge [SQLAlchemy: Single Table Inheritance, same column in childs][single-table-inheritance],
# hvis svar er skrevet af zzzeek, der er vedligeholder på SQLAlchemy, er løsningen,
# at man bruger SQLAlchemy's class decorator `declared_attr` og laver en form for
# property for hver kolonne, der skal være i den nedarvede klasse.
#
# [single-table-inheritance]: https://stackoverflow.com/a/17140952
#
# Følger man dette svar får man dog problemer, der ligner dét, der skulle løses, her
# ved at `TrigonometriskKoteforskel` definerer et felt, her `koteforskel`, der allerede
# er defineret på Observation (ja, Observation, ikke klassen GeometriskKoteforskel).
#
# Vi håbede, at man med Single Inheritance kunne fjerne attributerne `value1..15`
# fra `Observation`. Beholde man dem, forsvinder problemet, hvor to eller flere
# nedarvende klasser, her `GeometriskKoteforskel` og `TrigonometriskKoteforskel`,
# begge anvender eksempelvis `value1` på entiteten til en attribut `koteforskel`.
#
# I løsningen fra SO er det tilsyneladende muligt ikke at have en komplet mapping
# i moder-klassen og samtidig have flere nedarvende klasser lave en attribut
# med samme navn og samme kolonne i entiteten. Det virker bare ikke.
#
# To fremgangsmåder løser altså problemet:
#
# 1. Fortsæt med at lade klasserne nedarve fra samme moderklasse, og behold
#    attributterne `value1..15`. Dette virker, og man kan falde tilbage til
#    moderklassen som standard observationsklasse.
#
#    En ulempe ved denne fremgangsmåde er, at man får alle `value1..15`
#    attributter med i hvert objekt, hvilket kan være kostbart i hukommelse.
#
# 2. Efter definition af klassen `GeometriskKoteforskel` kan denne bruges i
#    eksempelvis `TrigonomiskKoteforskel` istedet for Observation, når man
#    definerer sine properties.
#
#    Eksempel:
#
#        class GeometriskKoteforskel(Observation):
#            (...)
#            @declared_attr
#            def koteforskel(cls):
#                # Virker kun for den første nedarvende klasse.
#                # På SO viser løsningen, at det skulle fungere for alle andre nedarvende klasser.
#                return Observation.__table__.c.get('value1', Column(Float))
#
#
#        class TrigonometriskKoteforskel(Observation):  # Brug fortsat Observation
#            (...)
#
#            @declared_attr
#            def koteforskel(cls):
#                # Dette virker for os.
#                return GeometriskKoteforskel.__table__.c.get('value1', Column(Float))
#
# Vælger vi mulighed 2, bliver koden for besværlig at vedligeholde, fordi
# de enkelte observationsklasser afhænger af hinanden i en lang kæde fra
# modeklassen `Observation`.
#
# Mulighed 1 er simplere at vedligeholde:
#
# * man kan fjerne en underklasse uden at det ødelægger funktionaliteten
#   af en underklasse, defineret efter denne.
#
# * man kan stadig bruge moderklassen `Observation`, da alle kolonnerne
#   i entiteten er tilgængelige fra denne klasse, selvom de ikke har
#   forklarende navne.
#
# Derfor bruger vi fremgangsmåde 1.
#


class Observation(FikspunktregisterObjekt):
    __tablename__ = "observation"
    id = Column(String, nullable=False, unique=True, default=fire.uuid)
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
    observationstidspunkt = Column(TIMESTAMP(timezone=True), nullable=False)
    antal = Column(Integer, nullable=False, default=1)
    gruppe = Column(Integer)
    observationstypeid = Column(
        Integer, ForeignKey("observationstype.observationstypeid")
    )
    observationstype = relationship(
        "ObservationsType", back_populates="observationer", lazy="joined"
    )
    sigtepunktid = Column(String(36), ForeignKey("punkt.id"))
    sigtepunkt = relationship("Punkt", foreign_keys=[sigtepunktid])
    opstillingspunktid = Column(String(36), ForeignKey("punkt.id"))
    opstillingspunkt = relationship("Punkt", foreign_keys=[opstillingspunktid])
    beregninger = relationship(
        "Beregning", secondary=beregning_observation, back_populates="observationer"
    )

    __mapper_args__ = {
        "polymorphic_identity": "observation",
        "polymorphic_on": observationstypeid,
    }


class GeometriskKoteforskel(Observation):
    """
    Observation foretaget ved Motoriseret Geometrisk Nivellement (MGL)

    """

    __mapper_args__ = {
        "polymorphic_identity": ObservationstypeID.geometrisk_koteforskel,
    }

    @declared_attr
    def koteforskel(cls):
        """Koteforskel / [m]"""
        return Observation.__table__.c.get("value1", Column(Float, nullable=False))

    @declared_attr
    def nivlængde(cls):
        """Nivellementslængde / [m]"""
        return Observation.__table__.c.get("value2", Column(Float))

    @declared_attr
    def opstillinger(cls):
        """Antal opstillinger"""
        return Observation.__table__.c.get("value3", Column(Integer))

    @declared_attr
    def eta_l(cls):
        """Variabel vedr. eta_1 (refraktion) / [m^3]"""
        return Observation.__table__.c.get("value4", Column(Float))

    @declared_attr
    def spredning_afstand(cls):
        """Empirisk spredning pr. afstandsenhed / [mm/sqrt(km)]"""
        return Observation.__table__.c.get("value5", Column(Float))

    @declared_attr
    def spredning_centrering(cls):
        """Empirisk centreringsfejl pr. opstilling / [mm]"""
        return Observation.__table__.c.get("value6", Column(Float))

    @declared_attr
    def præcisionsnivellement(cls):
        """Præcisionsnivellement [0, 1, 2, 3]"""
        return Observation.__table__.c.get("value7", Column(Integer))


class TrigonometriskKoteforskel(Observation):
    """
    Observation foretaget ved Motoriseret Trigonometrisk Nivellement (MTL)

    """

    __mapper_args__ = {
        "polymorphic_identity": ObservationstypeID.trigonometrisk_koteforskel
    }

    @declared_attr
    def koteforskel(cls):
        """Koteforskel / [m]"""
        return Observation.__table__.c.get("value1", Column(Float, nullable=False))

    @declared_attr
    def nivlængde(cls):
        """Nivellementslængde / [m]"""
        return Observation.__table__.c.get("value2", Column(Float))

    @declared_attr
    def opstillinger(cls):
        """Antal opstillinger"""
        return Observation.__table__.c.get("value3", Column(Integer))

    @declared_attr
    def spredning_afstand(cls):
        """Empirisk spredning pr. afstandsenhed / [mm/sqrt(km)]"""
        return Observation.__table__.c.get("value4", Column(Float))

    @declared_attr
    def spredning_centrering(cls):
        """Empirisk centreringsfejl pr. opstilling / [mm]"""
        return Observation.__table__.c.get("value5", Column(Float))


class Retning(Observation):
    """
    Horisontal retning med uret fra opstilling til sigtepunkt (reduceret til ellipsoiden)

    """

    __mapper_args__ = {"polymorphic_identity": ObservationstypeID.retning}

    @declared_attr
    def retning(cls):
        """Retning / [m]"""
        return Observation.__table__.c.get("value1", Column(Float, nullable=False))

    @declared_attr
    def varians_retning(cls):
        """Varians [for] retning hidrørende fra instrument, pr. sats / [rad^2]"""
        return Observation.__table__.c.get("value2", Column(Float))

    @declared_attr
    def varians_samlet(cls):
        """Samlet centreringsvarians for instrumentprisme / [m^2]"""
        return Observation.__table__.c.get("value3", Column(Integer))


class Horisontalafstand(Observation):
    """
    Horisontal afstand mellem opstilling og sigtepunkt (reduceret til ellipsoiden)

    """

    __mapper_args__ = {"polymorphic_identity": ObservationstypeID.horisontalafstand}

    @declared_attr
    def afstand(cls):
        """Afstand / [m]"""
        return Observation.__table__.c.get("value1", Column(Float, nullable=False))

    @declared_attr
    def varians_afstand(cls):
        """Afstandsafhængig varians afstandsmåler / [m^2 / m^2]"""
        return Observation.__table__.c.get("value2", Column(Float))

    @declared_attr
    def varians_samlet(cls):
        """Samlet varians for centrering af instrument og prisme, samt grundfejl på afstandsmåler / [m^2]"""
        return Observation.__table__.c.get("value3", Column(Integer))


class Skråafstand(Observation):
    """
    Skråafstand mellem opstilling og sigtepunkt

    """

    __mapper_args__ = {"polymorphic_identity": ObservationstypeID.skråafstand}

    @declared_attr
    def afstand(cls):
        """Afstand / [m]"""
        return Observation.__table__.c.get("value1", Column(Float, nullable=False))

    @declared_attr
    def varians_afstand(cls):
        """Afstandsafhængig varians afstandsmåler pr. måling / [m^2/m^2]"""
        return Observation.__table__.c.get("value2", Column(Float))

    @declared_attr
    def varians_samlet(cls):
        """Samlet varians for centrering af instrument og prisme, samt grundfejl på afstandsmåler pr. måling / [m^2]"""
        return Observation.__table__.c.get("value3", Column(Integer))


class Zenitvinkel(Observation):
    """
    Zenitvinkel mellem opstilling og sigtepunkt

    """

    __mapper_args__ = {"polymorphic_identity": ObservationstypeID.zenitvinkel}

    @declared_attr
    def vinkel(cls):
        """Zenitvinkel / [rad]"""
        return Observation.__table__.c.get("value1", Column(Float, nullable=False))

    @declared_attr
    def højde_instrument(cls):
        """Instrumenthøjde / [m]"""
        return Observation.__table__.c.get("value2", Column(Float))

    @declared_attr
    def højde_sigtepunkt(cls):
        """Højde sigtepunkt / [m]"""
        return Observation.__table__.c.get("value3", Column(Integer))

    @declared_attr
    def varians_vinkel(cls):
        """Varians zenitvinkel hidrørende fra instrument, pr. sats / [rad^2]"""
        return Observation.__table__.c.get("value4", Column(Float))

    @declared_attr
    def varians_samlet(cls):
        """Samlet varians instrumenthøjde/højde sigtepunkt / [m^2]"""
        return Observation.__table__.c.get("value5", Column(Integer))


class Vektor(Observation):
    """
    Vektor der beskriver koordinatforskellen fra punkt 1 til punkt 2 (v2-v1)

    """

    __mapper_args__ = {"polymorphic_identity": ObservationstypeID.vektor}

    @declared_attr
    def dx(cls):
        """dx [m]"""
        return Observation.__table__.c.get("value1", Column(Float, nullable=False))

    @declared_attr
    def dy(cls):
        """dy [m]"""
        return Observation.__table__.c.get("value2", Column(Float))

    @declared_attr
    def dz(cls):
        """dz [m]"""
        return Observation.__table__.c.get("value3", Column(Integer))

    @declared_attr
    def varians_afstand(cls):
        """Afstandsafhængig varians [m^2/m^2]"""
        return Observation.__table__.c.get("value4", Column(Float))

    @declared_attr
    def varians_samlet(cls):
        """Samlet varians for centrering af antenner [m^2]"""
        return Observation.__table__.c.get("value5", Column(Integer))

    @declared_attr
    def v_dx(cls):
        """Varians dx [m^2]"""
        return Observation.__table__.c.get("value6", Column(Float, nullable=False))

    @declared_attr
    def v_dy(cls):
        """Varians dy [m^2]"""
        return Observation.__table__.c.get("value7", Column(Float))

    @declared_attr
    def v_dz(cls):
        """Varians dz [m^2]"""
        return Observation.__table__.c.get("value8", Column(Integer))

    @declared_attr
    def cov_dxdy(cls):
        """Covarians dx, dy [m^2]"""
        return Observation.__table__.c.get("value9", Column(Float))

    @declared_attr
    def cov_dxdz(cls):
        """Covarians dx, dz [m^2]"""
        return Observation.__table__.c.get("value10", Column(Integer))

    @declared_attr
    def cov_dydz(cls):
        """Covarians dy, dz [m^2]"""
        return Observation.__table__.c.get("value11", Column(Integer))


class Nulobservation(Observation):
    """
    Observation nummer nul, indlagt fra start i observationstabellen,
    så der kan refereres til den i de mange beregningsevents der fører
    til population af koordinattabellen

    """

    __mapper_args__ = {"polymorphic_identity": ObservationstypeID.nulobservation}


class Srid(DeclarativeBase):
    __tablename__ = "sridtype"
    objektid = Column(Integer, primary_key=True)
    sridid = Column(Integer, unique=True, nullable=False)
    name = Column("srid", String(36), nullable=False, unique=True)
    beskrivelse = Column(String(4000))
    x = Column(String(4000))
    y = Column(String(4000))
    z = Column(String(4000))
