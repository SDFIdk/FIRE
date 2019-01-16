def test_hent_srid(firedb):
    key = "DK:DVR90"
    srid = firedb.hent_srid(key)
    assert srid.name == key
