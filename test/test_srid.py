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
