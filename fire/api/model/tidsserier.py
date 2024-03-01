from dataclasses import dataclass, fields
from datetime import datetime as dt
import time
from typing import List, Tuple, Type

import functools
import numpy as np
from numpy.polynomial import polynomial as P
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from scipy.stats import t, norm

from fire.matematik import xyz2neu
from fire.api.model import (
    FikspunktregisterObjekt,
    Observation,
    ObservationsLængde,
    ResidualKovarians,
    KoordinatKovarians,
    tidsserie_koordinat,
)
from fire.api.model.observationer import ObservationsLængde
from fire.api.model.punkttyper import Koordinat

__all__ = [
    "Tidsserie",
    "GNSSTidsserie",
    "HøjdeTidsserie",
]


def til_decimalår(date):
    """
    Stjålet fra StackOverflow og omdøbt:

    https://stackoverflow.com/a/6451892
    """

    def sinceEpoch(date):  # returns seconds since epoch
        return time.mktime(date.timetuple())

    s = sinceEpoch

    year = date.year
    startOfThisYear = dt(year=year, month=1, day=1)
    startOfNextYear = dt(year=year + 1, month=1, day=1)

    yearElapsed = s(date) - s(startOfThisYear)
    yearDuration = s(startOfNextYear) - s(startOfThisYear)
    fraction = yearElapsed / yearDuration

    return date.year + fraction


def beregn_fraktil_for_t_fordeling(q: float, dof: int = 0) -> float:
    """Returner den q'te fraktil for t-fordelingen med dof frihedsgrader."""
    return t.ppf(q, dof)


def beregn_fraktil_for_normalfordeling(q: float) -> float:
    """Returner den q'te fraktil for normalfordelingen."""
    return norm.ppf(q)


class TidsserietypeID:
    """
    ID for eksisterende tidsserietyper i FIRE-databasen.

    Notes
    -----
    ID'erne er fastsat i DDL-filerne for databasen og kan derfor fastsættes her.

    """

    gnss = 1
    højde = 2


class Tidsserie(FikspunktregisterObjekt):
    __tablename__ = "tidsserie"
    sagseventfraid = Column(String, ForeignKey("sagsevent.id"), nullable=False)
    sagsevent = relationship(
        "Sagsevent", foreign_keys=[sagseventfraid], back_populates="tidsserier"
    )
    sagseventtilid = Column(String, ForeignKey("sagsevent.id"), nullable=True)
    slettet = relationship(
        "Sagsevent",
        foreign_keys=[sagseventtilid],
        back_populates="tidsserier_slettede",
    )

    punktid = Column(String(36), ForeignKey("punkt.id"))
    punkt = relationship("Punkt")

    punktsamlingsid = Column(Integer, ForeignKey("punktsamling.objektid"))
    punktsamling = relationship("PunktSamling", back_populates="tidsserier")

    navn = Column(String, nullable=False)
    formål = Column("formaal", String, nullable=False)

    referenceramme = Column(String, nullable=False)
    sridid = Column(Integer, ForeignKey("sridtype.sridid"), nullable=False)
    srid = relationship("Srid", lazy="joined")

    tstype = Column(Integer, nullable=False)

    koordinater = relationship(
        "Koordinat",
        secondary=tidsserie_koordinat,
        back_populates="tidsserier",
        order_by=Koordinat.t,
    )

    __mapper_args__ = {
        "polymorphic_identity": "tidsserie",
        "polymorphic_on": tstype,
    }


class GNSSTidsserie(Tidsserie):
    __mapper_args__ = {
        "polymorphic_identity": TidsserietypeID.gnss,
    }

    @property
    def tidsseriegruppe(self):
        (_, gruppenavn, _) = self.navn.split("_")
        return gruppenavn

    @functools.cached_property
    def x(self) -> List[float]:
        """
        Liste med x-komponenter fra tidsseriens koordinater.

        Koordinatkomponenten er i geocentrisk repræsentation.
        """
        return [k.x for k in self.koordinater]

    @functools.cached_property
    def X(self) -> List[float]:
        """
        Liste med tidsseriens x-værdier normaliseret til tidsseriens første element.

        Koordinatkomponenten er i geocentrisk repræsentation.
        """
        x0 = self.x[0]
        return [x - x0 for x in self.x]

    @functools.cached_property
    def y(self) -> List[float]:
        """
        Liste med y-komponenter fra tidsseriens koordinater.

        Koordinatkomponenten er i geocentrisk repræsentation.
        """
        return [k.y for k in self.koordinater]

    @functools.cached_property
    def Y(self) -> List[float]:
        """
        Liste med tidsseriens y-værdier normaliseret til tidsseriens første element.

        Koordinatkomponenten er i geocentrisk repræsentation.
        """
        y0 = self.y[0]
        return [y - y0 for y in self.y]

    @functools.cached_property
    def z(self) -> List[float]:
        """
        Liste med z-komponenter fra tidsseriens koordinater.

        Koordinatkomponenten er i geocentrisk repræsentation.
        """
        return [k.z for k in self.koordinater]

    @functools.cached_property
    def Z(self) -> List[float]:
        """
        Liste med tidsseriens z-værdier normaliseret til tidsseriens første element.

        Koordinatkomponenten er i geocentrisk repræsentation.
        """
        z0 = self.z[0]
        return [z - z0 for z in self.z]

    @functools.cached_property
    def sx(self) -> List[float]:
        """
        Spredninger for tidsseriens x-komponenter.

        Spredning givet i milimeter.
        """
        return [k.sx for k in self.koordinater]

    @functools.cached_property
    def sy(self) -> List[float]:
        """
        Spredninger for tidsseriens y-komponenter.

        Spredning givet i milimeter.
        """
        return [k.sy for k in self.koordinater]

    @functools.cached_property
    def sz(self) -> List[float]:
        """
        Spredninger for tidsseriens z-komponenter.

        Spredning givet i milimeter.
        """
        return [k.sz for k in self.koordinater]

    @property
    def t(self) -> List[dt]:
        """
        Liste med t-komponenter fra tidsseriens koordinater givet som datetime objekt.
        """
        return [k.t for k in self.koordinater]

    @functools.cached_property
    def decimalår(self) -> List[float]:
        """
        Liste med t-komponenter fra tidsseriens koordinater givet i decimalår.
        """
        return [til_decimalår(k.t) for k in self.koordinater]

    @functools.cache
    def _neu(self):
        """
        Beregn topocentriske koordinatdifferencer for alle tre komponenter.

        Bruger fire.matematik.xyz2neu hvilket ikke nødvendigvis er den
        bedste løsning. Alternativt kan alle koordinater omregnes
        til længde, bredde og ellipsoidehøjde hvorefter
        storcirkelafstande mellem første og n'te punkte regnes med geod.
        Eller en version af xyz2neu der tager højde for ellipsoiden kan
        udvikles. Options, options, options...
        """
        # omtrentlig position, godt nok?
        lon, lat = self.punkt.geometri.koordinater
        return [xyz2neu(x, y, z, lat, lon) for x, y, z in zip(self.X, self.Y, self.Z)]

    @property
    def n(self):
        """
        Tidsseriens udvikling i nordlig retning, normaliseret til tidsseriens
        første element.
        """
        return [n for n, _, _ in self._neu()]

    @property
    def e(self):
        """
        Tidsseriens udvikling i østlig retning, normaliseret til tidsseriens
        første element.
        """
        return [e for _, e, _ in self._neu()]

    @property
    def u(self):
        """
        Tidsseriens udvikling i op-retningen, normaliseret til tidsseriens
        første element.
        """
        return [u for _, _, u in self._neu()]

    def _obs_liste(self, observationsklasse: Observation, attribut: str):
        observationer = []

        for k in self.koordinater:
            for obs in k.observationer:
                if isinstance(obs, observationsklasse):
                    observationer.append(obs.__getattribute__(attribut))
                    break
            else:
                observationer.append(None)

        return observationer

    @functools.cached_property
    def obslængde(self) -> List[float]:
        """
        Liste med observationslængder i timer for hver koordinat i tidsserien.

        Hvis den N'te koordinat ikke har observationslængde  registreret indsættes
        None i listen på plads N-1.
        """
        return self._obs_liste(ObservationsLængde, "varighed")

    @functools.cached_property
    def koordinatkovarians_xx(self) -> List[float]:
        """
        Returner liste med koordinatkovariansmatrixens xx-komponent for hver
        koordinat i tidsserien.

        Hvis den N'te koordinat ikke har koordinatkovariansmatrix registreret indsættes
        None i listen på plads N-1.
        """
        return self._obs_liste(KoordinatKovarians, "xx")

    @functools.cached_property
    def koordinatkovarians_xy(self) -> List[float]:
        """
        Returner liste med koordinatkovariansmatrixens xy-komponent for hver
        koordinat i tidsserien.

        Hvis den N'te koordinat ikke har koordinatkovariansmatrix registreret indsættes
        None i listen på plads N-1.
        """
        return self._obs_liste(KoordinatKovarians, "xy")

    @functools.cached_property
    def koordinatkovarians_xz(self) -> List[float]:
        """
        Returner liste med koordinatkovariansmatrixens xz-komponent for hver
        koordinat i tidsserien.

        Hvis den N'te koordinat ikke har koordinatkovariansmatrix registreret indsættes
        None i listen på plads N-1.
        """
        return self._obs_liste(KoordinatKovarians, "xz")

    @functools.cached_property
    def koordinatkovarians_yy(self) -> List[float]:
        """
        Returner liste med koordinatkovariansmatrixens yy-komponent for hver
        koordinat i tidsserien.

        Hvis den N'te koordinat ikke har koordinatkovariansmatrix registreret indsættes
        None i listen på plads N-1.
        """
        return self._obs_liste(KoordinatKovarians, "yy")

    @functools.cached_property
    def koordinatkovarians_yz(self) -> List[float]:
        """
        Returner liste med koordinatkovariansmatrixens yz-komponent for hver
        koordinat i tidsserien.

        Hvis den N'te koordinat ikke har koordinatkovariansmatrix registreret indsættes
        None i listen på plads N-1.
        """
        return self._obs_liste(KoordinatKovarians, "yz")

    @functools.cached_property
    def koordinatkovarians_zz(self) -> List[float]:
        """
        Returner liste med koordinatkovariansmatrixens zz-komponent for hver
        koordinat i tidsserien.

        Hvis den N'te koordinat ikke har koordinatkovariansmatrix registreret indsættes
        None i listen på plads N-1.
        """
        return self._obs_liste(KoordinatKovarians, "zz")

    @functools.cached_property
    def koordinatkovarians(self) -> List[Tuple[float]]:
        """
        Returnerer liste med koordinatkovarians tuple for hver koordinat i tidsserien.

        Hver tuple er på formen (xx, xy, xz, yy, yz, zz).

        Hvis den N'te koordinat ikke har koordinatkovariansmatrix registreret indsættes
        None i listen på plads N-1.
        """
        return list(
            zip(
                self.koordinatkovarians_xx,
                self.koordinatkovarians_xy,
                self.koordinatkovarians_xz,
                self.koordinatkovarians_yy,
                self.koordinatkovarians_yz,
                self.koordinatkovarians_zz,
            )
        )

    @functools.cached_property
    def residualkovarians_xx(self) -> List[float]:
        """
        Returner liste med residualkovariansmatrixens xx-komponent for hver
        koordinat i tidsserien.

        Hvis den N'te koordinat ikke har residualkovariansmatrix registreret indsættes
        None i listen på plads N-1.
        """
        return self._obs_liste(ResidualKovarians, "xx")

    @functools.cached_property
    def residualkovarians_xy(self) -> List[float]:
        """
        Returner liste med residualkovariansmatrixens xy-komponent for hver
        koordinat i tidsserien.

        Hvis den N'te koordinat ikke har residualkovariansmatrix registreret indsættes
        None i listen på plads N-1.
        """
        return self._obs_liste(ResidualKovarians, "xy")

    @functools.cached_property
    def residualkovarians_xz(self) -> List[float]:
        """
        Returner liste med residualkovariansmatrixens xz-komponent for hver
        koordinat i tidsserien.

        Hvis den N'te koordinat ikke har residualkovariansmatrix registreret indsættes
        None i listen på plads N-1.
        """
        return self._obs_liste(ResidualKovarians, "xz")

    @functools.cached_property
    def residualkovarians_yy(self) -> List[float]:
        """
        Returner liste med residualkovariansmatrixens yy-komponent for hver
        koordinat i tidsserien.

        Hvis den N'te koordinat ikke har residualkovariansmatrix registreret indsættes
        None i listen på plads N-1.
        """
        return self._obs_liste(ResidualKovarians, "yy")

    @functools.cached_property
    def residualkovarians_yz(self) -> List[float]:
        """
        Returner liste med residualkovariansmatrixens yz-komponent for hver
        koordinat i tidsserien.

        Hvis den N'te koordinat ikke har residualkovariansmatrix registreret indsættes
        None i listen på plads N-1.
        """
        return self._obs_liste(ResidualKovarians, "yz")

    @functools.cached_property
    def residualkovarians_zz(self) -> List[float]:
        """
        Returner liste med residualkovariansmatrixens zz-komponent for hver
        koordinat i tidsserien.

        Hvis den N'te koordinat ikke har residualkovariansmatrix registreret indsættes
        None i listen på plads N-1.
        """
        return self._obs_liste(ResidualKovarians, "zz")

class HypoteseTest:
    """Foretag statistisk hypotesetest."""

    def __init__(
        self, std_est: float, kritiskværdi: float, H0: float = 0, alpha: float = 0.05
    ):
        self.H0 = H0
        self.alpha = alpha
        self.std_est = std_est
        self.kritiskværdi = kritiskværdi

    @property
    def score(self) -> float:
        """Returner hypotesetestens score."""
        return abs(self.H0 / self.std_est)

    @property
    def H0accepteret(self) -> bool:
        """
        Evaluer hypotesetestens resultat.

        Hvis H0 accepteres, betyder det at der ikke kan påvises en signifikant forskel
        mellem den testede parameter og referencen.
        Omvendt, hvis H0 forkastes, betyder det at test-parameteren med signifikant
        sandsynlighed adskiller sig fra referencen.
        """
        return bool(self.score < self.kritiskværdi)


class HøjdeTidsserie(Tidsserie):
    __mapper_args__ = {
        "polymorphic_identity": TidsserietypeID.højde,
    }
