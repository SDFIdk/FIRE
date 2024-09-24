import pytest

import fire
from fire.cli import FireDb
from fire.api.model import (
    Tidsserie,
    HøjdeTidsserie,
    GNSSTidsserie,
)


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
