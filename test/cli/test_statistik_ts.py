import numpy as np
import pytest

from fire.api.model.tidsserier import PolynomieRegression1D
from fire.cli.ts.statistik_ts import (
    Statistik,
    StatistikGnss,
    StatistikGnssSamlet,
    StatistikHts,
    beregn_statistik_til_gnss_rapport,
    beregn_statistik_til_hts_rapport,
)


def test_beregn_statistik_til_gnss_rapport(gnsstidsserie):

    x = np.linspace(-1, 1, 1000)

    gnsstidsserie.forbered_lineær_regression(x, x)

    gnsstidsserie.beregn_lineær_regression()

    statistik = beregn_statistik_til_gnss_rapport(
        gnsstidsserie, alpha=0.05, reference_hældning=0
    )

    assert isinstance(statistik, StatistikGnss)

    statistik = beregn_statistik_til_gnss_rapport(
        gnsstidsserie, alpha=0.05, reference_hældning=0, er_samlet=True
    )

    assert isinstance(statistik, StatistikGnssSamlet)


def test_beregn_statistik_til_hts_rapport(højdetidsserie):

    x = np.linspace(-1, 1, 1000)

    højdetidsserie.forbered_lineær_regression(x, x)

    højdetidsserie.beregn_lineær_regression()

    statistik = beregn_statistik_til_hts_rapport(højdetidsserie)

    assert isinstance(statistik, StatistikHts)
