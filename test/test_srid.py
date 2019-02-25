def test_hent_srid(firedb):
    key = "EPSG:5799"
    srid = firedb.hent_srid(key)
    assert srid.name == key
