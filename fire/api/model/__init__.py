"""SQLAlchemy models for the application
"""
import enum

import sqlalchemy.ext.declarative
from sqlalchemy import Column, Integer, DateTime, String, func
from sqlalchemy.dialects.oracle import TIMESTAMP

from fire.enumtools import enum_values


class BetterBehavedEnum(sqlalchemy.types.TypeDecorator):
    """
    SQLAlchemy ignorer som standard værdierne i tilknyttet labels i en Enum.
    Denne klasse sørger for at de korrekte værdier indsættes, sådan at

    Boolean.FALSE oversættes til 'false' og ikke 'FALSE'.
    """

    def __init__(self, enumtype: enum.Enum, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._enumtype = enumtype

    def process_bind_param(self, value, dialect):
        try:
            return value.value
        except AttributeError:
            return value

    def process_result_value(self, value, dialect):
        if value not in enum_values(self._enumtype):
            return
        return self._enumtype(value)


class IntEnum(BetterBehavedEnum):
    """Add an integer enum class"""

    impl = sqlalchemy.Integer


class StringEnum(BetterBehavedEnum):
    """Add an integer enum class"""

    impl = sqlalchemy.String


class ReprBase(object):
    """
    Udvid SQLAlchemys Base klasse.

    Giver pænere repr() output. Modificeret fra StackOverflow:
    https://stackoverflow.com/a/54034962
    """

    def __repr__(self):
        class_ = self.__class__.__name__

        attrs = []
        for col in self.__table__.columns:
            try:
                attrs.append((col.name, getattr(self, col.name)))
            except AttributeError:
                # Der er ikke altid et en til en match mellem kolonnenavn og attributnavn
                try:
                    # Mest almindeligt er at et "id" udelades i attributnavnet ...
                    attributnavn = col.name.replace("id", "")
                    attrs.append((attributnavn, getattr(self, attributnavn)))
                except AttributeError:
                    # ... og hvis mapningen er anderledes springes den over
                    continue

        sattrs = ", ".join("{}={!r}".format(*x) for x in sorted(attrs))
        return f"{class_}({sattrs})"


# base class for SQLAlchemy declarative models. Inherits ReprBase to get nicer __repr__ behaviour
DeclarativeBase = sqlalchemy.ext.declarative.declarative_base(cls=ReprBase)


class RegisteringFraObjekt(DeclarativeBase):
    # SQLALchemy knows abstract classes do not map to a table.
    # If class is not declared abstract then SQLAlchemy whines about missing table declaration.
    __abstract__ = True
    objektid = Column(Integer, primary_key=True)
    _registreringfra = Column(
        "registreringfra",
        TIMESTAMP(timezone=True),
        nullable=False,
        default=func.current_timestamp(),
    )

    @property
    def registreringfra(self):
        return self._registreringfra


class RegisteringTidObjekt(DeclarativeBase):
    # SQLALchemy knows abstract classes do not map to a table.
    # If class is not declared abstract then SQLAlchemy whines about missing table declaration.
    __abstract__ = True
    objektid = Column(Integer, primary_key=True)
    _registreringfra = Column(
        "registreringfra",
        TIMESTAMP(timezone=True),
        nullable=False,
        default=func.current_timestamp(),
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
    objektid = Column(Integer, primary_key=True)
    dir_skitser = Column(String, nullable=False)


# Expose these types
from .geometry import *
from .punkttyper import *
from .sagstyper import *
