from fire.api import FireDb
from fire.api.model import ObservationsType, Boolean


def test_hent_observationstype(firedb: FireDb):
    o = firedb.hent_observationstype("retning")
    assert isinstance(o, ObservationsType)


def test_hent_observationstyper(firedb: FireDb):
    ot = list(firedb.hent_observationstyper())
    assert len(ot) > 1
    assert all([isinstance(x, ObservationsType) for x in ot])


def test_indset_observationstype(firedb: FireDb):
    ot = ObservationsType(
        name="absolut_tyngde",
        beskrivelse="Absolut gravimetrisk observation",
        value1="tyngdeacceleration",
        sigtepunkt=Boolean.FALSE,
    )
    firedb.indset_observationstype(ot)
    typ = firedb.hent_observationstype("absolut_tyngde")

    assert typ.value1 == ot.value1

    firedb.session.delete(typ)
    firedb.session.commit()
