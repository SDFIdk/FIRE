import pytest
from sqlalchemy.exc import NoResultFound

import fire
from fire.api.model import (
    GNSSTidsserie,
    HøjdeTidsserie,
)
from fire.api.model.observationer import (
    KoordinatKovarians,
    ResidualKovarians,
    ObservationsLængde,
)


def test_opret_tidsserie(firedb, sagsevent, punkt, punktsamling, srid, koordinatfabrik):
    """Test oprettelse af en tidsserie."""
    # Tidsserie med punktsamling og jessenkoordinat
    punktsamling.punkter.append(punkt)
    punkt.koordinater = [koordinatfabrik() for _ in range(5)]

    ts1 = HøjdeTidsserie(
        sagsevent=sagsevent,
        punkt=punkt,
        punktsamling=punktsamling,
        formål="Test",
        navn=f"TS-{fire.uuid()}",
        srid=srid,
        koordinater=punkt.koordinater,
    )

    firedb.session.add(ts1)
    firedb.session.flush()

    assert isinstance(ts1, HøjdeTidsserie)
    assert ts1.objektid is not None
    assert ts1.registreringfra is not None
    assert ts1.sagseventfraid == sagsevent.id

    # Tidsserie uden punktsamling og jessenkoordinat
    ts2 = HøjdeTidsserie(
        sagsevent=sagsevent,
        punkt=punkt,
        formål="Test",
        navn=f"TS-{fire.uuid()}",
        srid=srid,
        koordinater=punkt.koordinater,
    )

    firedb.session.add(ts2)
    firedb.session.flush()

    assert isinstance(ts2, HøjdeTidsserie)
    assert ts2.objektid is not None
    assert ts2.registreringfra is not None
    assert ts2.sagseventfraid == sagsevent.id


def test_luk_tidsserie(firedb, højdetidsserie, sagsevent):
    """Test at FireDb.luk_tidsserie() virker som forventet."""
    firedb.session.flush()
    firedb.luk_tidsserie(højdetidsserie, sagsevent)

    assert højdetidsserie.registreringtil is not None


def test_udvid_tidsserie(firedb, højdetidsserie, koordinatfabrik):
    """Test at flere koordinater kan tilføjes en tidsserie."""
    firedb.session.flush()
    n = len(højdetidsserie.koordinater)

    koordinat = koordinatfabrik()
    koordinat.punkt = højdetidsserie.punkt
    højdetidsserie.koordinater.append(koordinat)
    firedb.session.flush()

    assert len(højdetidsserie.koordinater) == n + 1


def test_hent_tidsserie_fra_punkt(firedb):
    punkt = firedb.hent_punkt("K-63-19113")
    assert len(punkt.tidsserier) == 1
    assert len(punkt.tidsserier[0].koordinater) == 4


def test_hent_tidsserie_fra_navn(firedb):
    ts = firedb.hent_tidsserie("RDIO_5D_IGb08")

    assert ts.punkt.ident == "RDIO"
    assert len(ts.koordinater) == 10

    with pytest.raises(NoResultFound):
        firedb.hent_tidsserie("Findes ikke")


def test_hent_tidsserier_fra_søgetekst(firedb):
    tidsserier = firedb.hent_tidsserier("HTS_AARHUS", tidsserieklasse=HøjdeTidsserie)

    assert len(tidsserier) == 3

    tidsserier = firedb.hent_tidsserier("_5D_IG", tidsserieklasse=GNSSTidsserie)

    assert len(tidsserier) == 2

    tidsserier = firedb.hent_tidsserier("Findes ikke")

    assert len(tidsserier) == 0


def test_tidsserie_koordinater_observationer(firedb):
    """
    Test at koordinater og observationer er korrekt tilknyttede i en tidsserie.

    Vi tager udgangspunkt i '5D_IGb14_RDO1', der har tre koordinater i tidsserien,
    med hver tre forskellige observationer tilknyttet de enkelte koordinater.
    """

    ts = firedb.hent_tidsserie("RDO1_5D_IGb14")

    for koordinat in ts.koordinater:
        assert len(koordinat.beregninger[0].observationer) == 3
        for obs in koordinat.beregninger[0].observationer:
            assert isinstance(
                obs, (ObservationsLængde, KoordinatKovarians, ResidualKovarians)
            )
