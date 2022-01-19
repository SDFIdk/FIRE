from pathlib import Path

import pytest
from sqlalchemy.exc import DatabaseError

import fire
from fire.api import FireDb
from fire.api.model import (
    Punkt,
    Grafik,
    Sag,
    Sagsevent,
    SagseventInfo,
    EventType,
)

JPG = Path("test/data/IMG_20180215_074401.jpg")
PNG = Path("test/data/K-16-00843.png")


def test_grafik(firedb: FireDb, sag: Sag, punkt: Punkt):
    """Test oprettelse af et Grafik objekt)"""
    filnavn = f"{fire.uuid()}.png"

    with open(PNG, "rb") as f:
        g = Grafik(
            punkt=punkt,
            grafik=f.read(),
            type="skitse",
            mimetype="image/png",
            filnavn=filnavn,
        )

    firedb.indset_sagsevent(
        Sagsevent(
            sag=sag,
            sagseventinfos=[SagseventInfo(beskrivelse="Testindsættelse af grafik")],
            eventtype=EventType.GRAFIK_INDSAT,
            grafikker=[g],
        )
    )


def test_grafik_fra_fil(firedb: FireDb, punkt: Punkt):
    """Test oprettelse af et Grafik objekt"""

    g_png = Grafik.fra_fil(punkt=punkt, sti=PNG)
    g_jpg = Grafik.fra_fil(punkt=punkt, sti=JPG)

    assert g_png.filnavn == PNG.name
    assert g_jpg.filnavn == JPG.name
    assert g_png.mimetype == "image/png"
    assert g_jpg.mimetype == "image/jpeg"

    with open(PNG, "rb") as png_blob:
        assert png_blob.read() == g_png.grafik

    with open(JPG, "rb") as jpg_blob:
        assert jpg_blob.read() == g_jpg.grafik

    # vigtigt at rydde op efter `punkt`, der i sin fixture bliver tilføjet
    # firedb.session men ikke commit()'ed. Hvis ikke der køres et rollback
    # fejler de næste tests pga "PendingRollback"
    firedb.session.rollback()


def test_grafik_unikke_filnavne(firedb: FireDb, sag: Sag, sagsevent: Sagsevent):
    """Test at der ikke kan oprettes filnavnedupletter"""
    filnavn = f"{fire.uuid()}.png"
    sagsevent.eventtype = EventType.PUNKT_OPRETTET
    p1 = Punkt(sagsevent=sagsevent)
    p2 = Punkt(sagsevent=sagsevent)

    g1 = Grafik(
        punkt=p1,
        filnavn=filnavn,
        mimetype="image/png",
        type="skitse",
        grafik=b"\xf3\xf5\xf8\x98",
    )

    g2 = Grafik(
        punkt=p2,
        filnavn=filnavn,
        mimetype="image/png",
        type="skitse",
        grafik=b"\xf3\xf5\xf8\x98",
    )

    with pytest.raises(DatabaseError):
        firedb.indset_sagsevent(
            Sagsevent(
                sag=sag,
                sagseventinfos=[
                    SagseventInfo(beskrivelse="Test fejl ved filnavnduplet")
                ],
                eventtype=EventType.GRAFIK_INDSAT,
                grafikker=[g1, g2],
            )
        )
    firedb.session.rollback()


def test_grafik_opdatering(firedb: FireDb, sag: Sag, punkt: Punkt):
    """Test at et nyt Grafik-objekt erstatter et gammelt korrekt"""
    filnavn = f"{fire.uuid()}.png"
    g1 = Grafik(
        punkt=punkt,
        filnavn=filnavn,
        mimetype="image/png",
        type="skitse",
        grafik=b"\xf3\xf5\xf8\x98",
    )

    firedb.indset_sagsevent(
        Sagsevent(
            sag=sag,
            sagseventinfos=[SagseventInfo(beskrivelse="Testindsættelse af grafik")],
            eventtype=EventType.GRAFIK_INDSAT,
            grafikker=[g1],
        )
    )

    g2 = Grafik(
        punkt=punkt,
        filnavn=filnavn,
        mimetype="image/png",
        type="skitse",
        grafik=b"\xf3\xf5\xf8\x99",
    )

    firedb.indset_sagsevent(
        Sagsevent(
            sag=sag,
            sagseventinfos=[SagseventInfo(beskrivelse="Opdatering af grafik")],
            eventtype=EventType.GRAFIK_INDSAT,
            grafikker=[g2],
        )
    )

    assert g1.registreringtil == g2.registreringfra
    assert g1.sagseventtilid == g2.sagseventfraid


def test_grafik_luk(firedb: FireDb, punkt: Punkt, sagsevent: Sagsevent):
    """Test at et Grafik objekt kan lukkes korrekt"""
    filnavn = f"{fire.uuid()}.png"
    g = Grafik(
        punkt=punkt,
        filnavn=filnavn,
        mimetype="image/png",
        type="skitse",
        grafik=b"\xf3\xf5\xf8\x98",
    )
    sagsevent.grafikker = [g]
    firedb.session.add(g)
    firedb.session.commit()

    assert g.registreringtil == None

    firedb.luk_grafik(g, sagsevent)
    assert g.registreringtil is not None
    assert g.sagsevent.eventtype == EventType.GRAFIK_NEDLAGT


def test_grafik_hent(firedb: FireDb, punkt: Punkt, sagsevent: Sagsevent):
    """Test FireDb.hent_grafik"""
    filnavn = f"{fire.uuid()}.png"
    g = Grafik(
        punkt=punkt,
        filnavn=filnavn,
        mimetype="image/png",
        type="skitse",
        grafik=b"\xf3\xf5\xf8\x98",
    )
    sagsevent.grafikker = [g]
    firedb.session.add(g)
    firedb.session.commit()

    gg = firedb.hent_grafik(filnavn)

    assert g.grafik == gg.grafik
    assert g.mimetype == gg.mimetype
    assert g.objektid == gg.objektid
