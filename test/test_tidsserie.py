import fire
from fire.api import FireDb
from fire.api.model import (
    Punkt,
    PunktGruppe,
    Tidsserie,
    EventType,
)


def test_tidsserie(firedb, punkt, punktgruppe, srid, koordinatfabrik):
    """Test oprettelse af en tidsserie."""
    # Tidsserie med punktgruppe og jessenkoordinat
    ts1 = Tidsserie(
        punkt=punkt,
        punktgruppe=punktgruppe,
        jessenkoordinat=koordinatfabrik(),
        referenceramme="FIRE",
        srid=srid,
        koordinater=[koordinatfabrik() for _ in range(5)],
    )

    firedb.session.flush()
    assert isinstance(ts1, Tidsserie)

    # Tidsserie uden punktgruppe og jessenkoordinat
    ts2 = Tidsserie(
        punkt=punkt,
        referenceramme="FIRE",
        srid=srid,
        koordinater=[koordinatfabrik() for _ in range(5)],
    )

    firedb.session.flush()
    assert isinstance(ts2, Tidsserie)


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
