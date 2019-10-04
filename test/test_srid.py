from fireapi.model import Srid


def test_hent_srid(firedb):
    key = "EPSG:5799"
    srid = firedb.hent_srid(key)
    assert srid.name == key


def test_hent_srider(firedb):
    srids = list(firedb.hent_srider())
    assert len(srids) > 1


def test_hent_srider_med_namespace(firedb):
    key = "EPSG"
    srids = list(firedb.hent_srider(key))
    assert len(srids) > 1
    assert all([s.name.startswith(key) for s in srids])


def test_indset_srid(firedb):
    si = Srid(name="EPSG:4977", beskrivelse="SWEREF99")
    firedb.indset_srid(si)
    so = firedb.hent_srid("EPSG:4977")

    assert so.name == si.name
