
from fireapi.model import *

def test_observation(firedb, observation):
    firedb.session.commit()

    o1 = firedb.session.query(Observation).get(observation.objectid)

    assert o1.objectid == observation.objectid

    
