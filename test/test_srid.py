def test_hent_srid(firedb):
    srid = firedb.hent_srid("DK:DVR90")
    assert srid.srid == "DVR:90"
