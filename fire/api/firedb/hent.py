"""
Funktionalitet til at hente diverse FIRE objekter
"""

from datetime import datetime
from typing import List, Optional
import re

from sqlalchemy import func, or_, and_
from sqlalchemy.orm import aliased, joinedload
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

from fire.api.firedb.base import FireDbBase
from fire.api.model import (
    Sag,
    Sagsevent,
    Sagsinfo,
    Punkt,
    PunktSamling,
    PunktInformation,
    PunktInformationType,
    GeometriObjekt,
    Grafik,
    Observation,
    ObservationsType,
    Geometry,
    Srid,
    Koordinat,
    Tidsserie,
)


class FireDbHent(FireDbBase):
    def hent_punkt(self, ident: str) -> Punkt:
        """
        Returnerer det første punkt der matcher 'ident'

        Prioriterer punkter som matcher 1:1.
        Hvis intet punkt findes udsendes en NoResultFound exception.
        """
        if ident not in self._cache["punkt"].keys():
            punkter = self.hent_punkter(ident)
            for pkt in punkter:
                if ident in pkt.identer:
                    punkt = pkt
                    break
            else:
                punkt = punkter[0]
                ident = punkt.ident

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
                    and_(
                        PunktInformationType.name.startswith("IDENT:"),
                        PunktInformationType.name != "IDENT:refgeo_id",
                    ),
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

    def hent_punkter_fra_uuid_liste(self, uuids: List[str]):
        """
        Hent alle punkter med punkt ID'er matchende listen `uuids`.

        Metoden tilbyder en hurtig måde at hente mange punkter ud af databasen på,
        når punkternes UUID'er er kendte, fx fra en observationsliste.
        """

        def chunks(lst, n):
            """Yield successive n-sized chunks from lst."""
            for i in range(0, len(lst), n):
                yield lst[i : i + n]

        punkter = []
        # Oracle er begrænset til IN-udtryk med 1000 elementer,
        # derfor hentes 1000 punkter ad gangen
        for subset in chunks(list(uuids), 1000):
            punkter.extend(
                self.session.query(Punkt)
                .filter(
                    Punkt.id.in_(subset),
                )
                .all()
            )

        return punkter

    def hent_alle_punkter(self) -> List[Punkt]:
        return self.session.query(Punkt).all()

    def hent_punktsamling(self, navn: str) -> PunktSamling:
        """
        Hent en punktsamling ud fra dens navn.

        Punktsamlingsnavne er unikke i FIRE, så der kan højest returneres
        en punktsamling ad gangen med denne metode.
        """
        return (
            self.session.query(PunktSamling)
            .filter(
                PunktSamling.navn == navn, PunktSamling._registreringtil == None
            )  # NOQA
            .one()
        )

    def hent_alle_punktsamlinger(self) -> list[PunktSamling]:
        """
        Hent alle punktsamlinger fra databasen.
        """
        return (
            self.session.query(PunktSamling)
            .filter(PunktSamling._registreringtil == None)  # NOQA
            .all()
        )

    def hent_tidsserie(self, navn: str) -> Tidsserie:
        """
        Hent en tidsserie ud fra dens navn.

        Tidsserienavne er unikke i FIRE, så der kan højest returneres
        en tidsserie ad gangen med denne metode.
        """
        return (
            self.session.query(Tidsserie)
            .filter(Tidsserie.navn == navn, Tidsserie._registreringtil == None)  # NOQA
            .one()
        )

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

    def hent_sagsevent(self, sagseventid: str) -> Sagsevent:
        """
        Hent et sagsevent ud fra dens sagseventid.

        Sagseventid'er behøver ikke være fuldstændige, funktionen forsøger at matche
        partielle sagseventid'er i samme stil som git håndterer commit hashes. I
        tilfælde af at søgningen med et partielt sagseventid resulterer i flere
        matches udsendes en sqlalchemy.orm.exc.MultipleResultsFound exception.
        """
        return self.session.query(Sagsevent).filter(Sagsevent.id.ilike(f"{sagseventid}%")).one()

    def hent_sager(
        self,
        søgetekst: str,
        aktive: bool = True,
        tid_fra: datetime = None,
        tid_til: datetime = None,
    ) -> list[Sag]:
        """
        Hent sager ud fra søgekriterier
        """

        try:
            sag = self.hent_sag(søgetekst)
        except (NoResultFound, MultipleResultsFound):
            pass
        else:
            return [sag]

        q = self.session.query(Sag).join(Sagsinfo)
        q = q.filter(Sagsinfo._registreringtil == None)

        if søgetekst is not None:
            q = q.filter(Sagsinfo.beskrivelse.ilike(f"%{søgetekst or ''}%"))

        fra_fejltekst = ""
        if tid_fra:
            fra_fejltekst = f"fra {tid_fra}"
            q = q.filter(Sag._registreringfra >= tid_fra)

        til_fejltekst = ""
        if tid_til:
            til_fejltekst = f"til {tid_til}"
            q = q.filter(Sag._registreringfra < tid_til)

        sager = q.all()

        # Filtrer på aktive sager
        if aktive:
            sager = [s for s in sager if s.aktiv]

        if not sager:
            raise NoResultFound(
                f"Ingen {'aktive ' if aktive else ''}sager med '{søgetekst}' fundet {fra_fejltekst} {til_fejltekst}"
            )

        return sager

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

    def hent_observationer_fra_opstillingspunkt(
        self,
        punkt: Punkt,
        tid_fra: Optional[datetime] = None,
        tid_til: Optional[datetime] = None,
        srid: Srid = None,
        kun_aktive: bool = True,
        observationsklasse: Observation = Observation,
        sigtepunkter: List[Punkt] = None,
    ) -> List[Observation]:
        """
        Hent observationer, hvor `punkt` var opstillingspunktet.

        """
        k = aliased(Koordinat)
        filtre = [observationsklasse.opstillingspunktid == punkt.id]
        if tid_fra is not None:
            filtre.append(observationsklasse.observationstidspunkt >= tid_fra)

        if tid_til is not None:
            filtre.append(observationsklasse.observationstidspunkt <= tid_til)

        if kun_aktive:
            filtre.append(observationsklasse._registreringtil == None)

        if sigtepunkter is not None:
            sigtepunktider = [sigtepunkt.id for sigtepunkt in sigtepunkter]
            filtre.append(observationsklasse.sigtepunktid.in_(sigtepunktider))

        query = self.session.query(observationsklasse)

        if srid is not None:
            query = query.join(k, k.punktid == observationsklasse.opstillingspunktid)
            filtre.append(k.sridid == srid.sridid)

        filtre_and = and_(*filtre)
        query = query.filter(filtre_and)
        return query.all()

    def hent_observationer_naer_opstillingspunkt(
        self,
        punkt: Punkt,
        afstand: float,
        tid_fra: Optional[datetime] = None,
        tid_til: Optional[datetime] = None,
    ) -> List[Observation]:
        g1 = aliased(GeometriObjekt)
        g2 = aliased(GeometriObjekt)
        return (
            self.session.query(Observation)
            .join(g1, Observation.opstillingspunktid == g1.punktid)
            .join(g2, g2.punktid == punkt.id)
            .filter(
                self._filter_observationer(
                    g1.geometri, g2.geometri, afstand, tid_fra, tid_til
                )
            )
            .all()
        )

    def hent_observationer_naer_geometri(
        self,
        geometri: Geometry,
        afstand: float,
        tid_fra: Optional[datetime] = None,
        tid_til: Optional[datetime] = None,
        observationsklasse: Observation = Observation,
    ) -> List[Observation]:
        """
        Parameters
        ----------
        geometri
            Forespørgslen udvælger alle geometriobjekter, der befinder
            sig inden for en given afstand af denne geometri.
        afstand
            Bufferafstand omkring geometri i meter.
        tid_fra
            Tidspunkt hvorfra observationerne skal have fundet sted.
        tid_til
            Tidspunkt hvortil observationerne skal have fundet sted.

        Returns
        -------
        List[Observation]
            En liste af alle de Observation'er der matcher søgekriterierne.
        """
        g = aliased(GeometriObjekt)
        filtre = self._filter_observationer(
            g.geometri, geometri, afstand, tid_fra, tid_til
        )
        return (
            self.session.query(observationsklasse)
            .join(
                g,
                g.punktid == observationsklasse.opstillingspunktid
                or g.punktid == observationsklasse.sigtepunktid,
            )
            .filter(filtre)
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

        try:
            # Prøv først at søge på det egentlige srid-navn.
            srid = (
                self.session.query(Srid)
                .filter(func.upper(Srid.name) == srid_filter)
                .one()
            )
        except NoResultFound as e:
            # Ellers søges på sridens korte navn
            srid = (
                self.session.query(Srid)
                .filter(func.upper(Srid.kortnavn) == srid_filter)
                .one()
            )

        return srid

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

    def hent_grafik(self, filnavn: str) -> Grafik:
        g = aliased(Grafik)
        return (
            self.session.query(g)
            .filter(g.filnavn == filnavn, g._registreringtil == None)  # NOQA
            .one()
        )
