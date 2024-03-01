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

class PolynomieRegression1D:
    """
    Foretag lineær regression over en tidsserie.
    """

    @dataclass
    class Statistik:
        TidsserieID: str
        GPSNR: str
        N: int
        N_binned: int
        dof: int
        ddof: int
        grad: int
        R2: float
        var_0: float
        std_0: float
        reference_hældning: float
        hældning: float
        var_hældning: float
        std_hældning: float
        ki_hældning_nedre: float
        ki_hældning_øvre: float
        mex: float
        mey: float
        T_test_accepteret: bool

        def __str__(self):
            header = ", ".join([str(field.name) for field in fields(self)])
            linje = ", ".join(
                [str(getattr(self, field.name)) for field in fields(self)]
            )
            return f"{header}\n{linje}"


    @dataclass
    class StatistikSamlet:
        var_samlet: float
        std_samlet: float
        var_hældning_samlet: float
        std_hældning_samlet: float
        ki_hældning_nedre_samlet: float
        ki_hældning_øvre_samlet: float
        Z_test_accepteret: bool

        def __str__(self):
            header = ", ".join([str(field.name) for field in fields(self)])
            linje = ", ".join(
                [str(getattr(self, field.name)) for field in fields(self)]
            )
            return f"{header}\n{linje}"


    def __init__(self, tidsserie: Tidsserie, x: list, y: list, grad: int = 1, **kwargs):
        self.tidsserie = tidsserie
        self.x = np.array(x)
        self.y = np.array(y)
        self.grad = grad
        self.hældning_reference = float("inf")

        self._var0 = None
        self.var_samlet = None

    @functools.cached_property
    def _A(self) -> np.ndarray:
        """Returner designmatricen A"""
        return P.polyvander(self.x, self.grad)

    @functools.cached_property
    def _invATA(self) -> np.ndarray:
        """
        Returner den inverse matrix af størrelsen (A^T * A)

        A er designmatricen for regressionen.
        """
        return np.linalg.inv(self._A.T @ self._A)

    def solve(self) -> None:
        """Løs hvad løses skal"""

        self.beta, [SSR, _, _, _] = P.polyfit(self.x, self.y, self.grad, full=True)

        if self.dof <= 0:
            raise ValueError(
                "Antallet af punkter er mindre end eller lig antallet af parametre."
            )

        if SSR.size == 0:
            raise ValueError(
                "Ligningssystemet har for lav rang. Kan forsøges fikset ved at normalisere data "
                "eller sætte polynomiegraden ned."
            )

        # Bruger item() istedet for SSR[0], så der smides fejl hvis SSR mod forventning
        # har mere end 1 element.
        self.SSR = SSR.item()

        self._var0 = self.SSR / self.dof
        self.var_samlet = self._var0

    @property
    def R2(self) -> float:
        """
        Returner bestemmelseskoefficienten R².

        R² måler mængden af variation i data der forklares af modellen.
        """
        return 1 - (self.SSR / np.sum((self.y - self.y.mean()) ** 2))

    @property
    def ddof(self) -> int:
        """Returner "Delta Degrees of Freedom"."""
        return self.grad + 1

    @property
    def N(self) -> int:
        """Returner længden af tidsserien."""
        return len(self.x)

    @property
    def dof(self) -> int:
        """Returner antallet af frihedsgrader."""
        return self.N - self.ddof

    @property
    def var0(self) -> float:
        """Returner estimeret varians af residualer."""
        return self._var0

    @property
    def mex(self) -> float:
        """Returner middelepokedatoen."""
        return sum(self.x) / self.N

    @property
    def mey(self) -> float:
        """Returner regressionens værdi ved middelepokedatoen."""
        return P.polyval(self.mex, self.beta)

    def KovariansMatrix(self, er_samlet: bool = False) -> np.ndarray:
        """
        Returner kovariansmatrix for estimerede parametre β₀, β₁ ...

        Kovariansmatricen har følgende struktur:
        COV =  [[Var(β₀)    , Cov(β₀,β₁)],
                [Cov(β₁, β₀), Var(β₁)   ]]
        """
        if er_samlet is False:
            var = self.var0
        elif er_samlet is True:
            var = self.var_samlet

        return var * self._invATA

    def VarBeta(self, er_samlet: bool = False) -> np.ndarray:
        """Returner den estimerede varians af de estimerede parametre βᵢ"""
        return np.diag(self.KovariansMatrix(er_samlet))

    def normaliser_data(
        self, a: float = -1, b: float = 1
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Normaliserer tidsseriens x og y data til intervallet [a , b]."""

        def normaliser(data: np.ndarray, a: float, b: float):
            return a + (b - a) * (data - data.min()) / (data.max() - data.min())

        x_norm = normaliser(self.x, a, b)
        y_norm = normaliser(self.y, a, b)

        return x_norm, y_norm

    def beregn_konfidensinterval(
        self, alpha: float = 0.05, er_samlet: bool = False
    ) -> np.ndarray:
        """
        Beregn Konfidensintervaller på estimerede parametre βᵢ givet signifikansniveau alpha

        Konfidensintervaller beregnes ud fra formlen:
            ki = βᵢ ± krit * Var(βᵢ)
        hvor krit er en kritisk værdi bestemt ud fra "fordeling" med signifikansniveau alpha.

        Output er af typen np.ndarray(2,N), hvor N er antallet af parametre.
        """
        if er_samlet:
            fraktil = beregn_fraktil_for_normalfordeling(1 - alpha / 2)
        else:
            fraktil = beregn_fraktil_for_t_fordeling(1 - alpha / 2, self.dof)

        delta_ki = fraktil * np.sqrt(self.VarBeta(er_samlet))

        return self.beta + np.outer([-1, 1], delta_ki)

    def beregn_prædiktioner(self, x_præd: List[float]) -> np.ndarray:
        """Beregn regressionens værdi i punkterne x_præd."""
        return P.polyval(x_præd, self.beta)

    def beregn_konfidensbånd(
        self,
        x_præd: List[float],
        y_præd: List[float] = None,
        *,
        alpha: float = 0.05,
        er_samlet: bool = False,
    ) -> np.ndarray:
        """
        Beregn Konfidensbånd for regressionslinjen.

        Konfidensbåndet er givet ved:
            pi = prædiktion ± delta_pi

        Output er af typen np.ndarray(2,N), hvor N er antallet af punkter i x_præd.
        """

        if er_samlet:
            var = self.var_samlet
            fraktil = beregn_fraktil_for_normalfordeling(1 - alpha / 2)
        else:
            var = self.var0
            fraktil = beregn_fraktil_for_t_fordeling(1 - alpha / 2, self.dof)

        if y_præd is None:
            y_præd = self.beregn_prædiktioner(x_præd)

        A_præd = P.polyvander(x_præd, self.grad)
        delta_pi = fraktil * np.sqrt(var * np.diag(A_præd @ self._invATA @ A_præd.T))

        return y_præd + np.outer([-1, 1], delta_pi)

    def beregn_hypotesetest(
        self,
        H0: float = 0,
        alpha: float = 0.05,
        er_samlet: bool = False,
    ) -> "HypoteseTest":
        """
        Beregn hypotesetest for den estimerede hældning.

        Returnerer objekt af typen HypoteseTest.
        """
        if er_samlet:
            kritiskværdi = beregn_fraktil_for_normalfordeling(1 - alpha / 2)
        else:
            kritiskværdi = beregn_fraktil_for_t_fordeling(1 - alpha / 2, self.dof)

        std_est = np.sqrt(self.VarBeta(er_samlet)[1])

        return HypoteseTest(
            H0=H0, alpha=alpha, std_est=std_est, kritiskværdi=kritiskværdi
        )

    def beregn_statistik(self, alpha: float, er_samlet: bool = False) -> None:
        """
        Metode til samlet beregning af statistik for tidsserien

        Resultaterne gemmes i `dict`-instanserne `self.statistik` og
        `self.statistik_samlet`.
        """

        H0 = self.hældning_reference - self.beta[1]

        # Er ikke samlet
        var_beta = self.VarBeta(er_samlet=False)[1]
        std_beta = np.sqrt(var_beta)
        konfidensinterval = self.beregn_konfidensinterval(alpha, er_samlet=False)
        T_test = self.beregn_hypotesetest(H0, alpha, er_samlet=False)

        self.statistik = self.Statistik(
            TidsserieID=self.tidsserie.navn,
            GPSNR=self.tidsserie.punkt.gnss_navn,
            N=len(self.tidsserie.koordinater),
            N_binned=self.N,
            dof=self.dof,
            ddof=self.ddof,
            grad=self.grad,
            R2=self.R2,
            var_0=self.var0,
            std_0=np.sqrt(self.var0),
            reference_hældning=self.hældning_reference,
            hældning=self.beta[1],
            var_hældning=var_beta,
            std_hældning=std_beta,
            ki_hældning_nedre=konfidensinterval[0, 1],
            ki_hældning_øvre=konfidensinterval[1, 1],
            mex=self.mex,
            mey=self.mey,
            T_test_accepteret=T_test.H0accepteret,
        )

        # er_samlet
        if not er_samlet:
            return

        var_beta_samlet = self.VarBeta(er_samlet=True)[1]
        std_beta_samlet = np.sqrt(var_beta_samlet)
        konfidensinterval_samlet = self.beregn_konfidensinterval(alpha, er_samlet=True)
        Z_test = self.beregn_hypotesetest(H0, alpha, er_samlet=True)

        self.statistik_samlet = self.StatistikSamlet(
            var_samlet=self.var_samlet,
            std_samlet=np.sqrt(self.var_samlet),
            var_hældning_samlet=var_beta_samlet,
            std_hældning_samlet=std_beta_samlet,
            ki_hældning_nedre_samlet=konfidensinterval_samlet[0, 1],
            ki_hældning_øvre_samlet=konfidensinterval_samlet[1, 1],
            Z_test_accepteret=Z_test.H0accepteret,
        )

    def generer_statistik_streng(self, **kwargs) -> Tuple[str, str]:
        """Genererer statistikstreng for tidsserien"""
        self.beregn_statistik(**kwargs)

        header = str(self.statistik).split("\n")[0]
        linje = str(self.statistik).split("\n")[1]

        if hasattr(self, "statistik_samlet"):
            header += ", " + str(self.statistik_samlet).split("\n")[0]
            linje += ", " + str(self.statistik_samlet).split("\n")[1]

        return header, linje


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
