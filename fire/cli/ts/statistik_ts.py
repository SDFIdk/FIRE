from dataclasses import dataclass, fields, asdict
from datetime import datetime

import numpy as np

from fire.api.model import (
    Tidsserie,
    GNSSTidsserie,
    HøjdeTidsserie,
    Punkt,
)


@dataclass
class Statistik:
    TidsserieID: str
    Ident: str
    N: int
    dof: int
    ddof: int
    grad: int
    R2: float
    var_0: float
    std_0: float
    hældning: float
    var_hældning: float
    std_hældning: float
    ki_hældning_nedre: float
    ki_hældning_øvre: float
    mex: float
    mey: float

    def __str__(self):
        header = ", ".join([str(field.name) for field in fields(self)])
        linje = ", ".join([str(getattr(self, field.name)) for field in fields(self)])
        return f"{header}\n{linje}"


@dataclass
class StatistikGnss(Statistik):
    N_binned: int
    reference_hældning: float
    T_test_H0accepteret: bool
    T_test_score: float
    T_test_alpha: float
    T_test_kritiskværdi: float


@dataclass
class StatistikGnssSamlet(StatistikGnss):
    var_samlet: float
    std_samlet: float
    var_hældning_samlet: float
    std_hældning_samlet: float
    ki_hældning_nedre_samlet: float
    ki_hældning_øvre_samlet: float
    Z_test_H0accepteret: bool
    Z_test_score: float
    Z_test_alpha: float
    Z_test_kritiskværdi: float


@dataclass
class StatistikHts(Statistik):
    Start: datetime
    Slut: datetime
    er_bevægelse_signifikant: bool
    alpha_bevægelse_signifikant: float


def beregn_statistik_til_gnss_rapport(
    tidsserie: GNSSTidsserie,
    alpha: float,
    reference_hældning: float,
    er_samlet: bool = False,
) -> StatistikGnss:
    """
    Metode til samlet beregning af statistik for en GNSS tidsserie

    Resultaterne gemmes i dataklassen `StatistikGnss`.
    """
    linreg = tidsserie.linreg

    # Er ikke samlet
    var_beta = linreg.VarBeta(er_samlet=False)[1]
    std_beta = np.sqrt(var_beta)
    konfidensinterval = linreg.beregn_konfidensinterval(alpha, er_samlet=False)
    T_test = linreg.beregn_hypotesetest_hældning(
        reference_hældning, alpha, er_samlet=False
    )

    statistik = StatistikGnss(
        TidsserieID=tidsserie.navn,
        Ident=tidsserie.punkt.gnss_navn,
        N=len(tidsserie),
        N_binned=linreg.N,
        dof=linreg.dof,
        ddof=linreg.ddof,
        grad=linreg.grad,
        R2=linreg.R2,
        var_0=linreg.var0,
        std_0=np.sqrt(linreg.var0),
        reference_hældning=reference_hældning,
        hældning=linreg.beta[1],
        var_hældning=var_beta,
        std_hældning=std_beta,
        ki_hældning_nedre=konfidensinterval[0, 1],
        ki_hældning_øvre=konfidensinterval[1, 1],
        mex=linreg.mex,
        mey=linreg.mey,
        T_test_H0accepteret=T_test.H0accepteret,
        T_test_score=T_test.score,
        T_test_alpha=T_test.alpha,
        T_test_kritiskværdi=T_test.kritiskværdi,
    )

    # er_samlet
    if not er_samlet:
        return statistik

    var_beta_samlet = linreg.VarBeta(er_samlet=True)[1]
    std_beta_samlet = np.sqrt(var_beta_samlet)
    konfidensinterval_samlet = linreg.beregn_konfidensinterval(alpha, er_samlet=True)
    Z_test = linreg.beregn_hypotesetest_hældning(
        reference_hældning, alpha, er_samlet=True
    )

    statistik_samlet = StatistikGnssSamlet(
        **asdict(statistik),
        var_samlet=linreg.var_samlet,
        std_samlet=np.sqrt(linreg.var_samlet),
        var_hældning_samlet=var_beta_samlet,
        std_hældning_samlet=std_beta_samlet,
        ki_hældning_nedre_samlet=konfidensinterval_samlet[0, 1],
        ki_hældning_øvre_samlet=konfidensinterval_samlet[1, 1],
        Z_test_H0accepteret=Z_test.H0accepteret,
        Z_test_score=Z_test.score,
        Z_test_alpha=Z_test.alpha,
        Z_test_kritiskværdi=Z_test.kritiskværdi,
    )
    return statistik_samlet


def beregn_statistik_til_hts_rapport(tidsserie: HøjdeTidsserie) -> StatistikHts:
    """
    Metode til samlet beregning af statistik for en HøjdeTidsserie

    Kalder den lineære regressions beregningsmetoder og returnerer de nødvendige
    statistik-parametre til brug i rapportering.

    NB! Konfidensintervaller, Trend-test og stabilitetstest foretages med default
    værdier for signifikansniveau, men der skal muligvis gives mulighed for at kunne
    indstille på dem.

    """
    linreg = tidsserie.linreg

    trend_test = tidsserie.signifikant_trend_test()

    # Er ikke samlet
    var_beta = linreg.VarBeta(er_samlet=False)[1]
    std_beta = np.sqrt(var_beta)
    konfidensinterval = linreg.beregn_konfidensinterval(er_samlet=False)

    statistik = StatistikHts(
        TidsserieID=tidsserie.navn,
        Ident=tidsserie.punkt.ident,
        N=len(tidsserie),
        dof=linreg.dof,
        ddof=linreg.ddof,
        grad=linreg.grad,
        R2=linreg.R2,
        var_0=linreg.var0,
        std_0=np.sqrt(linreg.var0),
        hældning=linreg.beta[1],
        var_hældning=var_beta,
        std_hældning=std_beta,
        ki_hældning_nedre=konfidensinterval[0, 1],
        ki_hældning_øvre=konfidensinterval[1, 1],
        mex=linreg.mex,
        mey=linreg.mey,
        Start=tidsserie.t[0],
        Slut=tidsserie.t[-1],
        er_bevægelse_signifikant=trend_test.H0accepteret,
        alpha_bevægelse_signifikant=trend_test.alpha,
    )

    return statistik
