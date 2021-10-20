"""
Funktionalitet til at hente diverse FIRE objekter
"""

from datetime import datetime
from typing import List, Optional
import re

from sqlalchemy import or_
from sqlalchemy.orm import aliased, joinedload
from sqlalchemy.orm.exc import NoResultFound
from fire.api import BaseFireDb

from fire.api.model import (
    Sag,
    Punkt,
    PunktInformation,
    PunktInformationType,
    GeometriObjekt,
    Observation,
    ObservationsType,
    Geometry,
    Srid,
)


class FireDbHent(BaseFireDb):
    def hent_punkt(self, ident: str) -> Punkt:
        """
        Returnerer det første punkt der matcher 'ident'

        Hvis intet punkt findes udsendes en NoResultFound exception.
        """
        if ident not in self._cache["punkt"].keys():
            punkt = self.hent_punkter(ident)[0]
            for idt in punkt.identer:
                self._cache["punkt"][idt] = punkt
            self._cache["punkt"][punkt.id] = punkt

        return self._cache["punkt"][ident]

    def hent_punkt_liste(
        self, identer: List[str], ignorer_ukendte: bool = True
    ) -> List[Punkt]:
        """
        Returnerer en liste af punkter der matcher identerne i listen `identer`.

        Hvis `ignorer_ukendte` sættes til False udløses en ValueError exception
        hvis et ident ikke kan matches med et Punkt i databasen.
        """
        punkter = []
        for ident in identer:
            try:
                punkter.append(self.hent_punkt(ident))
            except NoResultFound:
                if not ignorer_ukendte:
                    raise ValueError(f"Ident {ident} ikke fundet i databasen")

        return punkter

    def hent_punkter(self, ident: str) -> List[Punkt]:
        """
        Returnerer alle punkter der matcher 'ident'

        Hvis intet punkt findes udsendes en NoResultFound exception.
        """
        uuidmønster = re.compile(
            r"^[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}$"
        )
        kort_uuidmønster = re.compile(r"^[0-9A-Fa-f]{8}$")

        if uuidmønster.match(ident):
            result = (
                self.session.query(Punkt)
                .filter(Punkt.id == ident, Punkt._registreringtil == None)  # NOQA
                .all()
            )
        elif kort_uuidmønster.match(ident):
            result = (
                self.session.query(Punkt)
                .filter(
                    Punkt.id.startswith(ident), Punkt._registreringtil == None
                )  # NOQA
                .all()
            )
        else:
            result = (
                self.session.query(Punkt)
                .options(
                    joinedload(Punkt.geometriobjekter),
                    joinedload(Punkt.koordinater),
                )
                .join(PunktInformation)
                .join(PunktInformationType)
                .filter(
                    PunktInformationType.name.startswith("IDENT:"),
                    PunktInformation._registreringtil == None,  # NOQA
                    or_(
                        PunktInformation.tekst == ident,
                        PunktInformation.tekst == f"FO  {ident}",
                        PunktInformation.tekst == f"GL  {ident}",
                    ),
                    Punkt._registreringtil == None,  # NOQA
                )
                .all()
            )

        if not result:
            raise NoResultFound(f"Punkt med ident {ident} ikke fundet")

        return result

    def hent_alle_punkter(self) -> List[Punkt]:
        return self.session.query(Punkt).all()

    def hent_geometri_objekt(self, punktid: str) -> GeometriObjekt:
        go = aliased(GeometriObjekt)
        return (
            self.session.query(go)
            .filter(go.punktid == punktid, go._registreringtil == None)  # NOQA
            .one()
        )

    def hent_sag(self, sagsid: str) -> Sag:
        """
        Hent en sag ud fra dens sagsid.

        Sagsid'er behøver ikke være fuldstændige, funktionen forsøger at matche
        partielle sagsider i samme stil som git håndterer commit hashes. I
        tilfælde af at søgningen med et partielt sagsid resulterer i flere
        matches udsendes en sqlalchemy.orm.exc.MultipleResultsFound exception.
        """
        return self.session.query(Sag).filter(Sag.id.ilike(f"{sagsid}%")).one()

    def hent_alle_sager(self, aktive=True) -> List[Sag]:
        """
        Henter alle sager fra databasen.
        """
        return self.session.query(Sag).all()

    def hent_observationstype(self, name: str) -> ObservationsType:
        """
        Hent en ObservationsType ud fra dens navn.

        Parameters
        ----------
        observationstypeid : str
            Navn på observationstypen.

        Returns
        -------
        ObservationsType:
            Den første ObservationsType der matcher det angivne navn. None hvis
            ingen observationstyper matcher det søgte navn.
        """
        namefilter = name
        return (
            self.session.query(ObservationsType)
            .filter(ObservationsType.name == namefilter)
            .first()
        )

    def hent_observationstyper(self) -> List[ObservationsType]:
        """
        Henter alle ObservationsTyper.
        """
        return self.session.query(ObservationsType).all()

    def hent_observationer(self, ids: List[str]) -> List[Observation]:
        """
        Returnerer alle observationer fra databasen hvis id'er er indeholdt i listen
        `ids`. Hvis `ids` indeholder ID'er som ikke findes i databasen gives der
        *ikke* en fejlmelding.
        """
        return self.session.query(Observation).filter(Observation.id.in_(ids)).all()

    def hent_observationer_naer_opstillingspunkt(
        self,
        punkt: Punkt,
        afstand: float,
        tidfra: Optional[datetime] = None,
        tidtil: Optional[datetime] = None,
    ) -> List[Observation]:
        g1 = aliased(GeometriObjekt)
        g2 = aliased(GeometriObjekt)
        return (
            self.session.query(Observation)
            .join(g1, Observation.opstillingspunktid == g1.punktid)
            .join(g2, g2.punktid == punkt.id)
            .filter(
                self._filter_observationer(
                    g1.geometri, g2.geometri, afstand, tidfra, tidtil
                )
            )
            .all()
        )

    def hent_observationer_naer_geometri(
        self,
        geometri: Geometry,
        afstand: float,
        tidfra: Optional[datetime] = None,
        tidtil: Optional[datetime] = None,
    ) -> List[Observation]:
        """
        Parameters
        ----------
        geometri
            Enten en WKT-streng eller en instans af Geometry, der bruges til
            udvælge alle geometriobjekter der befinder sig inden for en given
            afstand af denne geometri.
        afstand
            Bufferafstand omkring geometri.
        tidfra

        tidtil
            asd

        Returns
        -------
        List[Observation]
            En liste af alle de Observation'er der matcher søgekriterierne.
        """
        g = aliased(GeometriObjekt)
        return (
            self.session.query(Observation)
            .join(
                g,
                g.punktid == Observation.opstillingspunktid
                or g.punktid == Observation.sigtepunktid,
            )
            .filter(
                self._filter_observationer(
                    g.geometri, geometri, afstand, tidfra, tidtil
                )
            )
            .all()
        )

    def hent_srid(self, sridid: str) -> Srid:
        """
        Hent et Srid objekt ud fra dets id.

        Parameters
        ----------
        sridid : str
            SRID streng, fx "EPSG:25832".

        Returns
        -------
        Srid
            Srid objekt med det angivne ID. None hvis det efterspurgte
            SRID ikke findes i databasen.
        """
        srid_filter = str(sridid).upper()
        return self.session.query(Srid).filter(Srid.name == srid_filter).one()

    def hent_srider(self, namespace: Optional[str] = None) -> List[Srid]:
        """
        Returnerer samtlige Srid objekter i databasen, evt. filtreret på namespace.

        Parameters
        ----------
        namespace: str - valgfri
            Return only Srids with the specified namespace. For instance "EPSG". If not
            specified all objects are returned.
            Returne kun SRID-objekter fra det valgte namespace, fx "EPSG". Hvis ikke
            angivet returneres samtlige SRID objekter fra databasen.

        Returns
        -------
        List[Srid]
        """
        if not namespace:
            return self.session.query(Srid).all()
        like_filter = f"{namespace}:%"
        return self.session.query(Srid).filter(Srid.name.ilike(like_filter)).all()

    def hent_punktinformationtype(self, infotype: str) -> PunktInformationType:
        if infotype not in self._cache["punktinfotype"]:
            typefilter = infotype
            pit = (
                self.session.query(PunktInformationType)
                .filter(PunktInformationType.name == typefilter)
                .first()
            )
            self._cache["punktinfotype"][infotype] = pit

        return self._cache["punktinfotype"][infotype]

    def hent_punktinformationtyper(self, namespace: Optional[str] = None):
        if not namespace:
            return self.session.query(PunktInformationType).all()
        like_filter = f"{namespace}:%"
        return (
            self.session.query(PunktInformationType)
            .filter(PunktInformationType.name.ilike(like_filter))
            .all()
        )
