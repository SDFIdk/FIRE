from datetime import datetime as dt
import pytest

import numpy as np

import fire
from fire.cli import FireDb
from fire.api.model import (
    Tidsserie,
    HøjdeTidsserie,
    GNSSTidsserie,
)
from fire.api.model.tidsserier import til_decimalår


def test_tidsserie_attributter(firedb: FireDb):
    """
    Test at man kan trække de forventede attributter ud med Tidsserie-api'et.

    Vi tager udgangspunkt i 'HTS_AARHUS_K-63-19113', der har fire koordinater i tidsserien.
    """

    ts = firedb.hent_tidsserie("HTS_AARHUS_K-63-19113")

    # Test implementering af __len__
    assert len(ts) == 4

    assert ts.referenceramme == ts.srid.kortnavn

    assert isinstance(ts, HøjdeTidsserie)
    assert hasattr(ts, "kote")
    assert hasattr(ts, "sz")

    assert len(ts.kote) == len(ts.sz)

    for k, sz in zip(ts.kote, ts.sz):
        assert isinstance(k, float)
        assert isinstance(sz, float)


def test_til_decimålår(firedb: FireDb):

    assert til_decimalår(dt(3000, 1, 1, 0, 0)) == 3000
    assert til_decimalår(dt(2025, 1, 1, 0, 0)) == 2025
    assert til_decimalår(dt(1700, 1, 1, 0, 0)) == 1700

    # Tjek at to ens datoer i forskellige år giver samme fraktion
    fraktion_1 = til_decimalår(dt(987, 10, 11, 0, 0)) - 987
    fraktion_2 = til_decimalår(dt(2345, 10, 11, 0, 0)) - 2345

    assert np.isclose(fraktion_1, fraktion_2)

    # Tjek at vi kan regne en tidsserie om til decimalår
    ts = firedb.hent_tidsserie("RDIO_5D_IGb08")
    assert len(ts.decimalår) == 10

    return
