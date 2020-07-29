from datetime import datetime, timezone
from typing import List, Optional
from pathlib import Path
import os
import re
import configparser
import getpass

from sqlalchemy import create_engine, func, event, and_, or_, inspect
from sqlalchemy.orm import sessionmaker, aliased
from sqlalchemy.orm.exc import NoResultFound

from fire.api.model import (
    RegisteringTidObjekt,
    FikspunktregisterObjekt,
    Sag,
    Punkt,
    PunktInformation,
    PunktInformationType,
    GeometriObjekt,
    Konfiguration,
    Koordinat,
    Observation,
    ObservationsType,
    Bbox,
    Sagsevent,
    Sagsinfo,
    Beregning,
    Geometry,
    EventType,
    Srid,
)


class FireDb(object):
    def __init__(self, connectionstring=None, debug=False):
        """

        Parameters
        ----------
        connectionstring : str
            Connection string til FIRE databasen.
            På formen 'user:pass@host:port/dbname[?key=value&key=value...]'
        debug: bool
            Hvis sat til True spyttes debug information ud på stdout. Kan
            omdirigeres ved at angive en anden logger til self.engine.
        """

        self._cache = {
            "punkt": {},
            "punktinfotype": {},
        }

        self.dialect = "oracle+cx_oracle"
        self.config = self._read_config()
        if connectionstring:
            self.connectionstring = connectionstring
        else:
            self.connectionstring = self._build_connection_string()

        self.engine = create_engine(
            f"{self.dialect}://{self.connectionstring}",
            connect_args={"encoding": "UTF-8", "nencoding": "UTF-8"},
            echo=debug,
        )
        self.sessionmaker = sessionmaker(bind=self.engine)
        self.session = self.sessionmaker(autoflush=False)

        @event.listens_for(self.sessionmaker, "before_flush")
        def listener(thissession, flush_context, instances):
            for obj in thissession.deleted:
                if isinstance(obj, RegisteringTidObjekt):
                    obj._registreringtil = func.sysdate()
                    thissession.add(obj)

    # region "Hent" methods

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
        if uuidmønster.match(ident):
            result = (
                self.session.query(Punkt)
                .filter(Punkt.id == ident, Punkt._registreringtil == None)  # NOQA
                .all()
            )
        else:
            result = (
                self.session.query(Punkt)
                .join(PunktInformation)
                .join(PunktInformationType)
                .filter(
                    PunktInformationType.name.startswith("IDENT:"),
                    or_(
                        PunktInformation.tekst == ident,
                        PunktInformation.tekst.like(f"FO  %{ident}"),
                        PunktInformation.tekst.like(f"GL  %{ident}"),
                    ),
                    Punkt._registreringtil == None,  # NOQA
                )
                .all()
            )

        if not result:
            raise NoResultFound

        return result

    def hent_geometri_objekt(self, punktid: str) -> GeometriObjekt:
        go = aliased(GeometriObjekt)
        return (
            self.session.query(go)
            .filter(go.punktid == punktid, go._registreringtil == None)  # NOQA
            .one()
        )

    def hent_alle_punkter(self) -> List[Punkt]:
        return self.session.query(Punkt).all()

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

    def soeg_geometriobjekt(self, bbox) -> List[GeometriObjekt]:
        if not isinstance(bbox, Bbox):
            bbox = Bbox(bbox)
        return (
            self.session.query(GeometriObjekt)
            .filter(func.sdo_filter(GeometriObjekt.geometri, bbox) == "TRUE")
            .all()
        )

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

    # endregion

    # region "Indset" methods

    def indset_sag(self, sag: Sag):
        if not self._is_new_object(sag):
            raise Exception(f"Sag allerede tilføjet databasen: {sag}")
        if len(sag.sagsinfos) < 1:
            raise Exception("Mindst et SagsInfo objekt skal tilføjes Sagen")
        if sag.sagsinfos[-1].aktiv != "true":
            raise Exception("Sidst SagsInfo på sagen skal have aktiv = 'true'")
        self.session.add(sag)
        self.session.commit()

    def indset_sagsevent(self, sagsevent: Sagsevent):
        if not self._is_new_object(sagsevent):
            raise Exception(f"Sagsevent allerede tilføjet databasen: {sagsevent}")
        if len(sagsevent.sagseventinfos) < 1:
            raise Exception("At least one sagseventinfo must be added to the sagsevent")
            raise Exception("Mindst et SagseventInfo skal tilføjes Sag")
        self.session.add(sagsevent)
        self.session.commit()

    def indset_flere_punkter(self, sagsevent: Sagsevent, punkter: List[Punkt]) -> None:
        """Indsæt flere punkter i punkttabellen, alle under samme sagsevent

        Parameters
        ----------
        sagsevent: Sagsevent
            Nyt (endnu ikke persisteret) sagsevent.

            NB: Principielt ligger "indset_flere_punkter" på et højere API-niveau
            end "indset_punkter", så det bør overvejes at generere sagsevent her.
            Argumentet vil så skulle ændres til "sagseventtekst: str", og der vil
            skulle tilføjes et argument "sag: Sag". Alternativt kan sagseventtekst
            autogenereres her ("oprettelse af punkterne nn, mm, ...")

        punkter: List[Punkt]
            De punkter der skal persisteres under samme sagsevent

        Returns
        -------
        None

        """
        # Check at alle punkter er i orden
        for punkt in punkter:
            if not self._is_new_object(punkt):
                raise Exception(f"Punkt allerede tilføjet databasen: {punkt}")
            if len(punkt.geometriobjekter) != 1:
                raise Exception(
                    "Der skal tilføjes et (og kun et) GeometriObjekt til punktet"
                )

        self._check_and_prepare_sagsevent(sagsevent, EventType.PUNKT_OPRETTET)

        for punkt in punkter:
            punkt.sagsevent = sagsevent
            for geometriobjekt in punkt.geometriobjekter:
                if not self._is_new_object(geometriobjekt):
                    raise Exception(
                        "Punktet kan ikke henvise til et eksisterende GeometriObjekt"
                    )
                geometriobjekt.sagsevent = sagsevent
            for punktinformation in punkt.punktinformationer:
                if not self._is_new_object(punktinformation):
                    raise Exception(
                        "Punktet kan ikke henvise til et eksisterende PunktInformation objekt"
                    )
                punktinformation.sagsevent = sagsevent
            self.session.add(punkt)

        self.session.commit()

    def indset_punkt(self, sagsevent: Sagsevent, punkt: Punkt):
        if not self._is_new_object(punkt):
            raise Exception(f"Punkt er allerede tilføjet databasen: {punkt}")
        if len(punkt.geometriobjekter) != 1:
            raise Exception(
                "Der skal tilføjes et (og kun et) GeometriObjekt til punktet"
            )
        self._check_and_prepare_sagsevent(sagsevent, EventType.PUNKT_OPRETTET)
        punkt.sagsevent = sagsevent
        for geometriobjekt in punkt.geometriobjekter:
            if not self._is_new_object(geometriobjekt):
                raise Exception(
                    "Punktet kan ikke henvise til et eksisterende GeometriObjekt"
                )
            geometriobjekt.sagsevent = sagsevent
        for punktinformation in punkt.punktinformationer:
            if not self._is_new_object(punktinformation):
                raise Exception(
                    "Punktet kan ikke henvise til et eksisterende PunktInformation objekt"
                )
            punktinformation.sagsevent = sagsevent
        self.session.add(punkt)
        self.session.commit()

    def indset_punktinformation(
        self, sagsevent: Sagsevent, punktinformation: PunktInformation
    ):
        if not self._is_new_object(punktinformation):
            raise Exception(
                f"PunktInformation allerede tilføjet databasen: {punktinformation}"
            )
        self._check_and_prepare_sagsevent(sagsevent, EventType.PUNKTINFO_TILFOEJET)
        punktinformation.sagsevent = sagsevent
        self.session.add(punktinformation)
        self.session.commit()

    def indset_punktinformationtype(self, punktinfotype: PunktInformationType):
        if not self._is_new_object(punktinfotype):
            raise Exception(
                f"PunktInformationType allerede tilføjet databasen: {punktinfotype}"
            )
        n = self.session.query(func.max(PunktInformationType.infotypeid)).one()[0]
        if n is None:
            n = 0
        punktinfotype.infotypeid = n + 1
        self.session.add(punktinfotype)
        self.session.commit()

    def indset_observation(self, sagsevent: Sagsevent, observation: Observation):
        if not self._is_new_object(observation):
            raise Exception(f"Observation allerede tilføjet databasen: {observation}")
        self._check_and_prepare_sagsevent(sagsevent, EventType.OBSERVATION_INDSAT)
        observation.sagsevent = sagsevent
        self.session.add(observation)
        self.session.commit()

    def indset_observationstype(self, observationstype: ObservationsType):
        if not self._is_new_object(observationstype):
            raise Exception(
                f"ObservationsType allerede tilføjet databasen: {observationstype}"
            )
        n = self.session.query(func.max(ObservationsType.observationstypeid)).one()[0]
        if n is None:
            n = 0
        observationstype.observationstypeid = n + 1
        self.session.add(observationstype)
        self.session.commit()

    def indset_beregning(self, sagsevent: Sagsevent, beregning: Beregning):
        if not self._is_new_object(beregning):
            raise Exception(f"Beregning allerede tilføjet datbasen: {beregning}")

        self._check_and_prepare_sagsevent(sagsevent, EventType.KOORDINAT_BEREGNET)
        beregning.sagsevent = sagsevent
        for koordinat in beregning.koordinater:
            if not self._is_new_object(koordinat):
                raise Exception(f"Koordinat allerede tilføjet datbasen: {koordinat}")
            koordinat.sagsevent = sagsevent
        self.session.add(beregning)
        self.session.commit()

    def indset_srid(self, srid: Srid):
        if not self._is_new_object(srid):
            raise Exception(f"Srid allerede tilføjet datbasen: {srid}")

        n = self.session.query(func.max(Srid.sridid)).one()[0]
        if n is None:
            n = 0
        srid.sridid = n + 1
        self.session.add(srid)
        self.session.commit()

    # endregion

    # region "luk" methods

    def luk_sag(self, sag: Sag):
        """Sætter en sags status til inaktiv"""
        if not isinstance(sag, Sag):
            raise TypeError("'sag' er ikke en instans af Sag")

        current = sag.sagsinfos[-1]
        new = Sagsinfo(
            aktiv="false",
            journalnummer=current.journalnummer,
            behandler=current.behandler,
            beskrivelse=current.beskrivelse,
            sag=sag,
        )
        self.session.add(new)
        self.session.commit()

    def luk_punkt(self, punkt: Punkt, sagsevent: Sagsevent):
        """
        Luk et punkt.

        Lukker udover selve punktet også tilhørende geometriobjekt,
        koordinater og punktinformationer. Alle lukkede objekter tilknyttes
        samme sagsevent af typen EventType.PUNKT_NEDLAGT.

        Dette er den ultimative udrensning. BRUG MED OMTANKE!
        """
        if not isinstance(punkt, Punkt):
            raise TypeError("'punkt' er ikke en instans af Punkt")

        sagsevent.eventtype = EventType.PUNKT_NEDLAGT
        self._luk_fikspunkregisterobjekt(punkt, sagsevent, commit=False)
        self._luk_fikspunkregisterobjekt(
            punkt.geometriobjekter[-1], sagsevent, commit=False
        )

        for koordinat in punkt.koordinater:
            self._luk_fikspunkregisterobjekt(koordinat, sagsevent, commit=False)

        for punktinfo in punkt.punktinformationer:
            self._luk_fikspunkregisterobjekt(punktinfo, sagsevent, commit=False)

        for observation in punkt.observationer_fra:
            self._luk_fikspunkregisterobjekt(observation, sagsevent, commit=False)

        for observation in punkt.observationer_til:
            self._luk_fikspunkregisterobjekt(observation, sagsevent, commit=False)

        self.session.commit()

    def luk_koordinat(self, koordinat: Koordinat, sagsevent: Sagsevent):
        """
        Luk en koordinat.

        Hvis ikke allerede sat, ændres sagseventtypen til EventType.KOORDINAT_NEDLAGT.
        """
        if not isinstance(koordinat, Koordinat):
            raise TypeError("'koordinat' er ikke en instans af Koordinat")

        sagsevent.eventtype = EventType.KOORDINAT_NEDLAGT
        self._luk_fikspunkregisterobjekt(koordinat, sagsevent)

    def luk_observation(self, observation: Observation, sagsevent: Sagsevent):
        """
        Luk en observation.

        Hvis ikke allerede sat, ændres sagseventtypen til EventType.OBSERVATION_NEDLAGT.
        """
        if not isinstance(observation, Observation):
            raise TypeError("'observation' er ikk en instans af Observation")

        sagsevent.eventtype = EventType.OBSERVATION_NEDLAGT
        self._luk_fikspunkregisterobjekt(observation, sagsevent)

    def luk_punktinfo(self, punktinfo: PunktInformation, sagsevent: Sagsevent):
        """
        Luk en punktinformation.

        Hvis ikke allerede sat, ændres sagseventtypen til EventType.PUNKTINFO_FJERNET.
        """
        if not isinstance(punktinfo, PunktInformation):
            raise TypeError("'punktinfo' er ikke en instans af PunktInformation")

        sagsevent.eventtype = EventType.PUNKTINFO_FJERNET
        self._luk_fikspunkregisterobjekt(punktinfo, sagsevent)

    def luk_beregning(self, beregning: Beregning, sagsevent: Sagsevent):
        """
        Luk en beregning.

        Lukker alle koordinater der er tilknyttet beregningen.
        Hvis ikke allerede sat, ændres sagseventtypen til EventType.KOORDINAT_NEDLAGT.
        """
        if not isinstance(beregning, Beregning):
            raise TypeError("'beregning' er ikke en instans af Beregning")

        sagsevent.eventtype = EventType.KOORDINAT_NEDLAGT
        for koordinat in beregning.koordinater:
            self._luk_fikspunkregisterobjekt(koordinat, sagsevent, commit=False)
        self._luk_fikspunkregisterobjekt(beregning, sagsevent, commit=False)
        self.session.commit()

    @property
    def basedir_skitser(self):
        """Returner absolut del af sti til skitser."""
        konf = self._hent_konfiguration()
        return konf.dir_skitser

    @property
    def basedir_materiale(self):
        """Returner absolut del af sti til sagsmateriale."""
        konf = self._hent_konfiguration()
        return konf.dir_materiale

    def _hent_konfiguration(self):
        return (
            self.session.query(Konfiguration)
            .filter(Konfiguration.objektid == 1)
            .first()
        )

    # region Private methods

    def _luk_fikspunkregisterobjekt(
        self, objekt: FikspunktregisterObjekt, sagsevent: Sagsevent, commit: bool = True
    ):
        objekt._registreringtil = datetime.now(tz=timezone.utc)
        objekt.sagseventtilid = sagsevent.id

        self.session.add(objekt)
        if commit:
            self.session.commit()

    def _check_and_prepare_sagsevent(self, sagsevent: Sagsevent, eventtype: EventType):
        """
        Tjek at et Sagsevent er gyldigt i den sammehæng som eventtype angiver.

        sagsevent skal være et "nyt" objekt, forstået på den måde at det ikke
        må være tilføjet databasen allerede. Det skal have samme eventtype som
        angivet.
        """
        if not self._is_new_object(sagsevent):
            raise Exception(
                "Nye objekter kan ikke tilføjes et allerede eksisterende Sagsevent"
            )
        if sagsevent.eventtype is None:
            sagsevent.eventtype = eventtype
        elif sagsevent.eventtype != eventtype:
            raise Exception(
                f"'{sagsevent.eventtype}' sagsevent. Burde være {eventtype}"
            )

    def _filter_observationer(
        self,
        g1,
        g2,
        distance: float,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
    ):
        exps = [
            func.sdo_within_distance(
                g1, g2, "distance=" + str(distance) + " unit=meter"
            )
            == "TRUE"
        ]
        if from_date:
            exps.append(Observation.observationstidspunkt >= from_date)
        if to_date:
            exps.append(Observation.observationstidspunkt <= to_date)
        return and_(*exps)

    def _is_new_object(self, obj):
        """
        Tjek at objektet ikke allerede er tilføjet til databasne (= det er 'nyt').

        Parameters
        ----------
        obj: object
            Objekt der skal tjekkes.

        Returns
        -------
        bool
            True hvis objektet ikke er tilføjet databasen, ellers False.
        """
        # here are the five states:
        # state.transient   # !session & !identity_key
        # state.pending     # session & !identity_key
        # state.persistent  # session &  identity_key
        # state.detached    # !session &  identity_key
        # state.deleted     # session & identity_key, flushed but not committed. Commit
        #                     moves it to detached state
        insp = inspect(obj)
        return not (insp.persistent or insp.detached)

    def _read_config(self):
        # Used for controlling the database setup when running the test suite
        RC_NAME = "fire.ini"

        # Find settings file and read database credentials
        if os.environ.get("HOME"):
            home = Path(os.environ["HOME"])
        else:
            home = Path("")

        search_files = [
            home / Path(RC_NAME),
            home / Path("." + RC_NAME),
            Path("/etc") / Path(RC_NAME),
            Path("C:\\Users") / Path(getpass.getuser()) / Path(RC_NAME),
            Path("C:\\Users\\Default\\AppData\\Local\\fire") / Path(RC_NAME),
        ]

        for conf_file in search_files:
            if Path(conf_file).is_file():
                break
        else:
            raise EnvironmentError("Konfigurationsfil ikke fundet!")

        default_settings = {
            # se https://www.gnu.org/software/gama/manual/gama.html#Network-SQL-definition
            "network-attributes": {
                "axes-xy": "en",
                "angles": "left-handed",
                "epoch": 0.0,
            },
            # se https://www.gnu.org/software/gama/manual/gama.html#Network-parameters
            "network-parameters": {
                "algorithm": "gso",
                "angles": 400,
                "conf-pr": 0.95,
                "cov-band": 0,
                "ellipsoid": "grs80",
                "latitude": 55.7,
                "sigma-act": "apriori",
                "sigma-apr": 1.0,
                "tol-abs": 1000.0,
                "update-constrained-coordinates": "no",
            },
        }

        parser = configparser.ConfigParser()
        parser.read_dict(default_settings)
        parser.read(conf_file)
        return parser

    def _build_connection_string(self):
        """Konstruer connection-string til databasen."""

        username = self.config.get("connection", "username")
        password = self.config.get("connection", "password")
        hostname = self.config.get("connection", "hostname")
        database = self.config.get("connection", "database")
        port = self.config.get("connection", "port", fallback=1521)

        return f"{username}:{password}@{hostname}:{port}/{database}"

    # endregion
