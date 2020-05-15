"""SQLAlchemy models for the application
"""
import sqlalchemy.ext.declarative
from sqlalchemy import Column, Integer, DateTime, String, func


class IntEnum(sqlalchemy.types.TypeDecorator):
    """Add an integer enum class"""

    impl = sqlalchemy.Integer

    def __init__(self, enumtype, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._enumtype = enumtype

    def process_bind_param(self, value, dialect):
        return value.value

    def process_result_value(self, value, dialect):
        return self._enumtype(value)


class ReprBase(object):
    """Extend the base class
    Provides a nicer representation when a class instance is printed.
    Found on the SA wiki
    """

    def __repr__(self):
        return "%s(%s)" % (
            (self.__class__.__name__),
            ", ".join(
                [
                    "%s=%r" % (key, getattr(self, key))
                    for key in sorted(self.__dict__.keys())
                    if not key.startswith("_")
                ]
            ),
        )


# base class for SQLAlchemy declarative models. Inherits ReprBase to get nicer __repr__ behaviour
DeclarativeBase = sqlalchemy.ext.declarative.declarative_base(cls=ReprBase)


class RegisteringFraObjekt(DeclarativeBase):
    # SQLALchemy knows abstract classes do not map to a table.
    # If class is not declared abstract then SQLAlchemy whines about missing table declaration.
    __abstract__ = True
    objectid = Column(Integer, primary_key=True)
    _registreringfra = Column(
        "registreringfra",
        DateTime(timezone=True),
        nullable=False,
        default=func.sysdate(),
    )

    @property
    def registreringfra(self):
        return self._registreringfra


class RegisteringTidObjekt(DeclarativeBase):
    # SQLALchemy knows abstract classes do not map to a table.
    # If class is not declared abstract then SQLAlchemy whines about missing table declaration.
    __abstract__ = True
    objectid = Column(Integer, primary_key=True)
    _registreringfra = Column(
        "registreringfra",
        DateTime(timezone=True),
        nullable=False,
        default=func.sysdate(),
    )
    _registreringtil = Column("registreringtil", DateTime(timezone=True))

    @property
    def registreringfra(self):
        return self._registreringfra

    @property
    def registreringtil(self):
        return self._registreringtil


class Konfiguration(DeclarativeBase):
    """
    Konfigurationstabel for FIRE.

    Tabellen har det særpræg at der kun kan indlæses en række i den.
    Den indeholder derfor altid den nye udgave af opsætningen. Tabellen
    er skabt for at kunne holde styr på systemspecifikke detaljer, der
    kan ændre sig over tid, fx basestier på et filsystem.
    """

    __tablename__ = "konfiguration"
    objectid = Column(Integer, primary_key=True)
    dir_skitser = Column(String, nullable=False)
    dir_materiale = Column(String, nullable=False)


# Expose these types
from .geometry import *
from .punkttyper import *
from .sagstyper import *
