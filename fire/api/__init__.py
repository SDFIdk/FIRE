import os
import configparser
import getpass
from pathlib import Path

from sqlalchemy import create_engine, func, event, inspect
from sqlalchemy.orm import sessionmaker

from fire.api.model import (
    RegisteringTidObjekt,
    FikspunktregisterObjekt,
    Konfiguration,
    Sagsevent,
    EventType,
)


class BaseFireDb:
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
        self.config = self._read_config()

        self.db = db
        if db not in (None, "prod", "test", "ci"):
            raise ValueError(
                "'db' skal være en af følgende: 'prod', 'test', 'ci' eller None"
            )

        if connectionstring:
            self.connectionstring = connectionstring
        else:
            self.connectionstring = self._build_connection_string(db)

        self._cache = {
            "punkt": {},
            "punktinfotype": {},
        }

        self.dialect = "oracle+cx_oracle"
        self.engine = create_engine(
            f"{self.dialect}://{self.connectionstring}",
            connect_args={"encoding": "UTF-8", "nencoding": "UTF-8"},
            echo=debug,
            execution_options=self._exe_opt,
        )
        self.sessionmaker = sessionmaker(bind=self.engine)
        self.session = self.sessionmaker(autoflush=False)

        @event.listens_for(self.sessionmaker, "before_flush")
        def listener(thissession, flush_context, instances):
            for obj in thissession.deleted:
                if isinstance(obj, RegisteringTidObjekt):
                    obj._registreringtil = func.current_timestamp()
                    thissession.add(obj)

    def _hent_konfiguration(self):
        return (
            self.session.query(Konfiguration)
            .filter(Konfiguration.objektid == 1)
            .first()
        )

    def _luk_fikspunkregisterobjekt(
        self, objekt: FikspunktregisterObjekt, sagsevent: Sagsevent, commit: bool = True
    ):
        objekt._registreringtil = func.current_timestamp()
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
            "general": {"default_connection": "prod"},
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

    def _build_connection_string(self, db: str):
        """Konstruer connection-string til databasen."""
        if db is None:
            db = self.config.get("general", "default_connection")
            self.db = db

        con = f"{db}_connection"
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


from fire.api.indset import FireDbIndset
from fire.api.luk import FireDbLuk
from fire.api.hent import FireDbHent
from fire.api.firedb import FireDb
