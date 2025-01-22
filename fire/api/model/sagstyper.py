import enum
from typing import List

from sqlalchemy import Column, String, Integer, ForeignKey, LargeBinary
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
    GRAFIK_INDSAT = 10
    GRAFIK_NEDLAGT = 11
    PUNKTGRUPPE_MODIFICERET = 12
    PUNKTGRUPPE_NEDLAGT = 13
    TIDSSERIE_MODIFICERET = 14
    TIDSSERIE_NEDLAGT = 15


class Sag(RegisteringFraObjekt):
    __tablename__ = "sag"
    id = Column(String(36), nullable=False, default=fire.uuid)
    sagsevents = relationship(
        "Sagsevent", order_by="Sagsevent.objektid", back_populates="sag"
    )
    sagsinfos = relationship(
        "Sagsinfo", order_by="Sagsinfo.objektid", back_populates="sag"
    )

    def ny_sagsevent(
        self,
        beskrivelse: str,
        materialer: List[bytes] = [],
        htmler: List[str] = [],
        id: str = None,
        **kwargs,
    ) -> "Sagsevent":
        """
        Fabrik til oprettelse af nye sagsevents.

        Oprettede sagsevents er altid tilknyttet sagen de blev skabt fra. Sagseventtypen
        bestemmes automatisk ud fra det tilknyttede indhold.

        `kwargs` føres direkte videre til Sagsevent og skal altså være et gyldigt
        argument til Sagsevent. Fælgende muligheder er tilgængelige:

            punkter
            geometriobjekter
            beregninger
            koordinater
            observationer
            punktinformationer
            grafikker
            punktsamlinger
            tidsserier
            punkter_slettede
            geometriobjekter_slettede
            beregninger_slettede
            koordinater_slettede
            observationer_slettede
            punktinformationer_slettede
            grafikker_slettede
            punktsamlinger_slettede
            tidsserier_slettede
        """

        if not id:
            id = fire.uuid()

        # fmt: off
        # Bestem EventType ud fra data tilknyttet sagsevent
        eventtyper = {
            EventType.PUNKT_OPRETTET: ("punkter", "geometriobjekter"),
            EventType.PUNKT_NEDLAGT: ("punkter_slettede", "geometriobjekter_slettede"),
            EventType.KOORDINAT_BEREGNET: ("koordinater", "beregninger"),
            EventType.KOORDINAT_NEDLAGT: ("koordinater_slettede","beregninger_slettede"),
            EventType.OBSERVATION_INDSAT: ("observationer", None),
            EventType.OBSERVATION_NEDLAGT: ("observationer_slettede", None),
            EventType.PUNKTINFO_TILFOEJET: ("punktinformationer", None),
            EventType.PUNKTINFO_FJERNET: ("punktinformationer_slettede", None),
            EventType.GRAFIK_INDSAT: ("grafikker", None),
            EventType.GRAFIK_NEDLAGT: ("grafikker_slettede", None),
            EventType.PUNKTGRUPPE_MODIFICERET: ("punktsamlinger", None),
            EventType.PUNKTGRUPPE_NEDLAGT: ("punktsamlinger_slettede", None),
            EventType.TIDSSERIE_MODIFICERET: ("tidsserier", None),
            EventType.TIDSSERIE_NEDLAGT: ("tidsserier_slettede", None),
        }
        # fmt: on

        materialer = [SagseventInfoMateriale(materiale=m) for m in materialer]
        htmler = [SagseventInfoHtml(html=html) for html in htmler]
        si = SagseventInfo(
            beskrivelse=beskrivelse,
            materialer=materialer,
            htmler=htmler,
        )

        if not kwargs:
            # intet data tilknyttet, det må være en kommentar
            return Sagsevent(
                sag=self,
                id=id,
                sagseventinfos=[si],
                eventtype=EventType.KOMMENTAR,
                **kwargs,
            )

        objekter = list(kwargs.keys())
        for etype, (obligatorisk, valgfrit) in eventtyper.items():
            if not obligatorisk in objekter:
                continue
            objekter.remove(obligatorisk)

            if valgfrit:
                if valgfrit in objekter:
                    objekter.remove(valgfrit)

            if not objekter:
                return Sagsevent(
                    sag=self, id=id, sagseventinfos=[si], eventtype=etype, **kwargs
                )
        else:
            raise ValueError(
                f"Uventede objekter forsøgt tilknyttet sagsevent: {objekter}"
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
    punktsamlinger = relationship(
        "PunktSamling",
        order_by="PunktSamling.objektid",
        back_populates="sagsevent",
        foreign_keys="PunktSamling.sagseventfraid",
    )
    punktsamlinger_slettede = relationship(
        "PunktSamling",
        order_by="PunktSamling.objektid",
        back_populates="slettet",
        foreign_keys="PunktSamling.sagseventtilid",
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
    tidsserier = relationship(
        "Tidsserie",
        order_by="Tidsserie.objektid",
        back_populates="sagsevent",
        foreign_keys="Tidsserie.sagseventfraid",
    )
    tidsserier_slettede = relationship(
        "Tidsserie",
        order_by="Tidsserie.objektid",
        back_populates="slettet",
        foreign_keys="Tidsserie.sagseventtilid",
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
    grafikker = relationship(
        "Grafik",
        order_by="Grafik.objektid",
        back_populates="sagsevent",
        foreign_keys="Grafik.sagseventfraid",
    )
    grafikker_slettede = relationship(
        "Grafik",
        order_by="Grafik.objektid",
        back_populates="slettet",
        foreign_keys="Grafik.sagseventtilid",
    )

    @property
    def beskrivelse(self) -> str:
        if not self.sagseventinfos:
            return ""
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
    materiale = Column(LargeBinary, nullable=False)
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
