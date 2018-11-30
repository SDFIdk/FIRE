
from fireapi.model import *

def test_beregning(firedb, beregning):
    firedb.session.commit()

    b0 = firedb.session.query(Beregning).get(beregning.objectid)

    assert b0.objectid == beregning.objectid

    assert len(b0.observationer) == 2

    assert b0.observationer[0].beregninger[0].objectid == beregning.objectid
