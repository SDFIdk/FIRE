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
                name = col.name
                attr = getattr(self, name)
                # Nogle attributter har en MEGET lang tekstrepræsentation,
                # fx en blob fra Grafik-klassen. Vi korter den ned for at holde
                # overblikket simpelt
                if attr.__len__:
                    if len(attr) > 20:
                        attr = f"{attr[0:20]}..."

                attrs.append((name, attr))
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


# Expose these types
from .geometry import *
from .punkttyper import *
from .sagstyper import *
