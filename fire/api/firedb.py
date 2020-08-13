from datetime import datetime, timezone
from typing import List, Optional, Iterator
from pathlib import Path
from itertools import chain
import os
import configparser
import getpass

from sqlalchemy import create_engine, func, event, and_, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text

from fire.api.model import (
    RegisteringTidObjekt,
    FikspunktregisterObjekt,
    Punkt,
    PunktInformation,
    GeometriObjekt,
    Konfiguration,
    Observation,
    Bbox,
    Sagsevent,
    EventType,
    FikspunktsType,
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

    from ._firedb_hent import (
        hent_punkt,
        hent_punkt_liste,
        hent_punkter,
        hent_punkter_med_jokertegn,
        hent_geometri_objekt,
        hent_alle_punkter,
        hent_sag,
        hent_alle_sager,
        hent_observationstype,
        hent_observationstyper,
        hent_observationer,
        hent_observationer_naer_opstillingspunkt,
        hent_observationer_naer_geometri,
        hent_srid,
        hent_srider,
        hent_punktinformationtype,
        hent_punktinformationtyper,
    )

    from ._firedb_indset import (
        indset_sag,
        indset_sagsevent,
        indset_flere_punkter,
        indset_punkt,
        indset_punktinformation,
        indset_punktinformationtype,
        indset_observation,
        indset_observationstype,
        indset_beregning,
        indset_srid,
    )

    from ._firedb_luk import (
        luk_sag,
        luk_punkt,
        luk_koordinat,
        luk_observation,
        luk_punktinfo,
        luk_beregning,
    )

    def soeg_geometriobjekt(self, bbox) -> List[GeometriObjekt]:
        if not isinstance(bbox, Bbox):
            bbox = Bbox(bbox)
        return (
            self.session.query(GeometriObjekt)
            .filter(func.sdo_filter(GeometriObjekt.geometri, bbox) == "TRUE")
            .all()
        )

    def tilknyt_landsnumre(
        self, punkter: List[Punkt], fikspunktstyper: List[FikspunktsType],
    ) -> List[PunktInformation]:
        """
        Tilknytter et landsnummer til punktet hvis der ikke findes et i forvejen.

        Returnerer en liste med IDENT:landsnr PunktInformation'er for alle de fikspunkter i
        `punkter` som ikke i forvejen har et landsnummer. Hvis alle fikspunkter i `punkter`
        allerede har et landsnummer returneres en tom liste.

        Kun punkter i Danmark kan tildeles et landsnummer. Det forudsættes at punktet
        har et tilhørende geometriobjekt og er indlæst i databasen i forvejen.
        """

        landsnr = self.hent_punktinformationtype("IDENT:landsnr")

        uuider = []
        punkttyper = {}
        for punkt, fikspunktstype in zip(punkter, fikspunktstyper):
            if not punkt.geometri:
                raise AttributeError("Geometriobjekt ikke tilknyttet Punkt")

            # Ignorer punkter, der allerede har et landsnummer
            if landsnr in [pi.infotype for pi in punkt.punktinformationer]:
                continue
            uuider.append(f"'{punkt.id}'")
            punkttyper[punkt.id] = fikspunktstype

        if not uuider:
            return []

        distrikter = self._opmålingsdistrikt_fra_punktid(uuider)

        distrikt_punkter = {}
        for (distrikt, pktid) in distrikter:
            if distrikt not in distrikt_punkter.keys():
                distrikt_punkter[distrikt] = []
            distrikt_punkter[distrikt].append(pktid)

        landsnumre = {}
        for distrikt, pkt_ider in distrikt_punkter.items():
            brugte_løbenumre = self._løbenumre_i_distrikt(distrikt)

            for punktid in pkt_ider:
                for kandidat in self._generer_tilladte_løbenumre(punkttyper[punktid]):
                    if kandidat in brugte_løbenumre:
                        continue

                    landsnumre[punktid] = f"{distrikt}-{kandidat}"
                    brugte_løbenumre.append(kandidat)
                    break

        punktinfo = []
        for punktid, landsnummer in landsnumre.items():
            pi = PunktInformation(punktid=punktid, infotype=landsnr, tekst=landsnummer)
            punktinfo.append(pi)

        return punktinfo

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

    def _generer_tilladte_løbenumre(
        self, fikspunktstype: FikspunktsType
    ) -> Iterator[str]:
        """
        Returner en generator med alle tilladte løbenumre for en given type fikspunkt.

        Hjælpefunktion til tilknyt_landsnumre.
        """

        interval = lambda start, stop: (str(i).zfill(5) for i in range(start, stop + 1))

        if fikspunktstype == FikspunktsType.GI:
            return chain(interval(1, 10), interval(801, 8999))

        if fikspunktstype == FikspunktsType.MV:
            return interval(11, 799)

        if fikspunktstype == FikspunktsType.HØJDE:
            return chain(interval(9001, 10000), interval(19001, 19999))

        if fikspunktstype == FikspunktsType.JESSEN:
            return interval(81001, 81999)

        if fikspunktstype == FikspunktsType.HJÆLPEPUNKT:
            return interval(90001, 99999)

        if fikspunktstype == FikspunktsType.VANDSTANDSBRÆT:
            raise NotImplementedError(
                "Fikspunktstypen 'VANDSTANDSBRÆT' er endnu ikke understøttet"
            )

        raise ValueError("Ukendt fikspunktstype")

    def _opmålingsdistrikt_fra_punktid(self, uuider: List[str]):
        """
        Udtræk relevante opmålingsdistrikter, altså dem hvor de adspurgte punkter
        befinder sig i.

        Hjælpefunktion til tilknyt_landsnumre(). Defineret i seperat funktion
        med henblik på at kunne mocke den i unit tests.
        """
        statement = text(
            f"""SELECT hs.kode, go.punktid
                FROM geometriobjekt go
                JOIN herredsogn hs ON sdo_relate(hs.geometri, go.geometri, 'mask=contains') = 'TRUE'
                WHERE
                go.punktid IN ({','.join(uuider)})
            """
        )

        return self.session.execute(statement)

    def _løbenumre_i_distrikt(self, distrikt: str):
        """
        For et givent opmålingsdistrikt findes alle landsnumre på formen
        xx-yyy-*****, hvorefter løbenummrene (*****) udskilles og returneres
        i sorteret orden.

        Hjælpefunktion til tilknyt_landsnumre(). Defineret i seperat funktion
        med henblik på at kunne mocke den i unit tests.
        """
        landsnr = self.hent_punktinformationtype("IDENT:landsnr")
        sql = text(
            fr"""SELECT lbnr
                FROM (
                    SELECT
                        regexp_substr(tekst, '.*-.*-(.+)', 1, 1, '', 1) lbnr
                    FROM punktinfo
                    WHERE infotypeid={landsnr.infotypeid} AND REGEXP_LIKE(tekst, '{distrikt}-.+$')
                )
                ORDER BY lbnr ASC
                """
        )

        return [løbenummer for løbenummer in self.session.execute(sql)]

    def _hent_konfiguration(self):
        return (
            self.session.query(Konfiguration)
            .filter(Konfiguration.objektid == 1)
            .first()
        )

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
