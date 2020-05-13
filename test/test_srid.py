from fire.api.model import Srid


def test_hent_srid(firedb):
    # DK:TEST is created by the srid fixture, should be present when this test is run
    key = "DK:TEST"
    srid = firedb.hent_srid(key)
    assert srid.name == key


def test_indset_srid(firedb):
    si = Srid(name="EPSG:4977", beskrivelse="SWEREF99")
    firedb.indset_srid(si)
    so = firedb.hent_srid("EPSG:4977")

    assert so.name == si.name

    # ... and remove si again once we've finished using it
    firedb.session.delete(si)
    firedb.session.commit()


def test_hent_srider(firedb):
    srids = list(firedb.hent_srider())
    assert len(srids) > 1


def test_hent_srider_med_namespace(firedb):
    # DK:TEST is created by the srid fixture, should be present when this test is run
    key = "DK"
    srids = list(firedb.hent_srider(key))
    assert len(srids) >= 1
    assert all([s.name.startswith(key) for s in srids])
