import pytest
from fireapi import FireDb
from fireapi.model import ObservationType


def test_hent_observationtype(firedb: FireDb):
    o = firedb.hent_observationtype("retning")
    assert isinstance(o, ObservationType)


def test_hent_observationtyper(firedb: FireDb):
    ot = list(firedb.hent_observationtyper())
    assert len(ot) > 1
    assert all([isinstance(x, ObservationType) for x in ot])


@pytest.mark.skip(
    "Table OBSERVATIONTYPE does not use namespaces yet. See https://github.com/Kortforsyningen/FIRE-DDL/issues/57"
)
def test_hent_observationtyper_med_namespace(firedb: FireDb):
    ot = list(firedb.hent_observationtyper("OBS"))
    assert len(ot) > 1
    assert all([isinstance(x, ObservationType) for x in ot])


def test_indset_observationtype(firedb: FireDb):
    ot = ObservationType(
        name="absolut_tyngde",
        beskrivelse="Absolut gravimetrisk observation",
        value1="tyngdeacceleration",
        sigtepunkt="false",
    )
    firedb.indset_observationtype(ot)
    typ = firedb.hent_observationtype("absolut_tyngde")

    assert typ.value1 == ot.value1
