from datetime import datetime
from typing import (
    Optional,
    Mapping,
)

from sqlalchemy import (
    create_engine,
    func,
    event,
    and_,
    inspect,
)
from sqlalchemy.orm import sessionmaker

from fire.api.model import (
    RegisteringTidObjekt,
    FikspunktregisterObjekt,
    Sagsevent,
    EventType,
    Observation,
)
from fire.api.configuration import get_configuration


def new_cache() -> Mapping[str, dict]:
    return {
        "punkt": {},
        "punktinfotype": {},
    }


class FireDbBase:
    _dialect = "oracle+cx_oracle"
    _exe_opt = {}

    def __init__(self, db=None, connectionstring=None, debug=False):
        """

        Parameters
        ----------
        db: str
            Vælg databaseforbindelse defineret i fire.ini. Mulige valg er
                prod, test, ci og None
            Hvis None, vælges defaultdatabasen fra fire.ini, er denne ikke sat
            faldes tilbage på prod databaseforbindelsen.
        connectionstring : str
            Connection string til FIRE databasen.
            På formen 'user:pass@host:port/dbname[?key=value&key=value...]'

            connectionstring bruges hvis db også er angivet.
        debug: bool
            Hvis sat til True spyttes debug information ud på stdout. Kan
            omdirigeres ved at angive en anden logger til self.engine.

        """
        if db not in (None, "prod", "test", "ci"):
            raise ValueError(
                "'db' skal være en af følgende: 'prod', 'test', 'ci' eller None"
            )

        self.db = db
        self.debug = debug
        self._cache = new_cache()

        # Bliver oprettet her, fordi gama-modulerne skal have adgang til konfigurationsfilen.
        # Ellers kan man undlade at oprette `self.config`, da konfigurationsfilen kun anvendes
        # til at bygge en connection string når denne ikke er givet ved instantiering.
        self.config = get_configuration()

        if connectionstring:
            self.connectionstring = connectionstring
        else:
            self.connectionstring = self._build_connection_string()

        self.engine = self._create_engine()

        self.sessionmaker = sessionmaker(bind=self.engine)
        self.session = self.sessionmaker(autoflush=False, future=True)

        @event.listens_for(self.sessionmaker, "before_flush")
        def listener(thissession, flush_context, instances):
            for obj in thissession.deleted:
                if isinstance(obj, RegisteringTidObjekt):
                    obj._registreringtil = func.current_timestamp()
                    thissession.add(obj)

    def _create_engine(self):
        return create_engine(
            f"{self._dialect}://{self.connectionstring}",
            connect_args={"encoding": "UTF-8", "nencoding": "UTF-8"},
            echo=self.debug,
            execution_options=self._exe_opt,
            future=True,
        )

    def _luk_fikspunktregisterobjekt(
        self, objekt: FikspunktregisterObjekt, sagsevent: Sagsevent, commit: bool = True
    ):
        objekt._registreringtil = func.current_timestamp()
        objekt.slettet = sagsevent

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

    def _build_connection_string(self):
        """Konstruér connection string til databasen."""
        if self.db is None:
            self.db = self.config.get("general", "default_connection")

        con = f"{self.db}_connection"
        username = self.config.get(con, "username")
        password = self.config.get(con, "password")
        hostname = self.config.get(con, "hostname")
        database = self.config.get(con, "database", fallback="")
        service = self.config.get(con, "service", fallback="")
        method = self.config.get(con, "method", fallback="service")
        port = self.config.get(con, "port", fallback=1521)
        schema = self.config.get(con, "schema", fallback="fire_adm")

        self._exe_opt = {"schema_translate_map": {None: schema}}

        if method not in {"service", "database"}:
            raise ValueError(
                "fire.ini/method skal være enten 'database' eller 'service'"
            )

        if method == "service":
            if service == "":
                raise ValueError(
                    "fire.ini/service skal defineres når method er 'service'"
                )
            return f"{username}:{password}@{hostname}:{port}/?service_name={service}"

        if database == "":
            raise ValueError(
                "fire.ini/database skal defineres når method er 'database'"
            )
        return f"{username}:{password}@{hostname}:{port}/{database}"

    def _filter_observationer(
        self,
        g1,
        g2,
        distance: float,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        observationsklasse: Observation = Observation,
    ):
        # Lav en lille buffer om geometrien for at gøre den gyldig
        g2 = func.sdo_geom.sdo_buffer(g2, 0.005, 0.005)

        # Gå med livrem og seler og brug Oracle's egen valideringsfunktion til geometrier
        # Efter disse to manøvrer, skulle Oracle gerne returnere "forudsigelige" resultater
        exps = [func.sdo_geom.validate_geometry(g2, 0.005) == "TRUE"]

        exps.append(
            func.sdo_within_distance(
                g1, g2, "distance=" + str(distance) + " unit=meter"
            )
            == "TRUE"
        )
        if from_date:
            exps.append(observationsklasse.observationstidspunkt >= from_date)
        if to_date:
            exps.append(observationsklasse.observationstidspunkt <= to_date)
        return and_(*exps)
