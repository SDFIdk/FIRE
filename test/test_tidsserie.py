import pytest
from sqlalchemy.exc import NoResultFound

import fire
from fire.api import FireDb
from fire.api.model import (
    Punkt,
    PunktSamling,
    Tidsserie,
    EventType,
)
from fire.api.model.observationer import (
    KoordinatKovarians,
    ResidualKovarians,
    ObservationsLængde,
)


def test_opret_tidsserie(firedb, sagsevent, punkt, punktsamling, srid, koordinatfabrik):
    """Test oprettelse af en tidsserie."""
    # Tidsserie med punktsamling og jessenkoordinat
    ts1 = Tidsserie(
        sagsevent=sagsevent,
        punkt=punkt,
        punktsamling=punktsamling,
        formål="Test",
        navn=f"TS-{fire.uuid()}",
        referenceramme="FIRE",
        srid=srid,
        koordinater=[koordinatfabrik() for _ in range(5)],
    )

    firedb.session.flush()

    assert isinstance(ts1, Tidsserie)
    assert ts1.objektid is not None
    assert ts1.registreringfra is not None
    assert ts1.sagseventfraid == sagsevent.id

    # Tidsserie uden punktsamling og jessenkoordinat
    ts2 = Tidsserie(
        sagsevent=sagsevent,
        punkt=punkt,
        formål="Test",
        navn=f"TS-{fire.uuid()}",
        referenceramme="FIRE",
        srid=srid,
        koordinater=[koordinatfabrik() for _ in range(5)],
    )

    firedb.session.flush()

    assert isinstance(ts2, Tidsserie)
    assert ts2.objektid is not None
    assert ts2.registreringfra is not None
    assert ts2.sagseventfraid == sagsevent.id


def test_luk_tidsserie(firedb, tidsserie, sagsevent):
    """Test at FireDb.luk_tidsserie() virker som forventet."""
    firedb.session.flush()
    firedb.luk_tidsserie(tidsserie, sagsevent)

    assert tidsserie.registreringtil is not None


def test_udvid_tidsserie(firedb, tidsserie, koordinat):
    """Test at flere koordinater kan tilføjes en tidsserie."""
    firedb.session.flush()
    n = len(tidsserie.koordinater)

    tidsserie.koordinater.append(koordinat)
    firedb.session.flush()

    assert len(tidsserie.koordinater) == n + 1


def test_hent_tidsserie_fra_punkt(firedb):

    punkt = firedb.hent_punkt("K-63-19113")
    assert len(punkt.tidsserier) == 1
    assert len(punkt.tidsserier[0].koordinater) == 4


def test_hent_tidsserie_fra_navn(firedb):
    ts = firedb.hent_tidsserie("5D_IGb08_RDIO")

    assert ts.punkt.ident == "RDIO"
    assert len(ts.koordinater) == 10

    with pytest.raises(NoResultFound):
        firedb.hent_tidsserie("findes ikk")


def test_tidsserie_koordinater_observationer(firedb):
    """
    Test at koordinater og observationer er korrekt tilknyttede i en tidsserie.

    Vi tager udgangspunkt i '5D_IGb14_RDO1', der har tre koordinater i tidsserien,
    med hver tre forskellige observationer tilknyttet de enkelte koordinater.
    """

    ts = firedb.hent_tidsserie("5D_IGb14_RDO1")

    for koordinat in ts.koordinater:
        assert len(koordinat.beregninger[0].observationer) == 3
        for obs in koordinat.beregninger[0].observationer:
            assert isinstance(
                obs, (ObservationsLængde, KoordinatKovarians, ResidualKovarians)
            )
