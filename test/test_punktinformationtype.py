from fire.api.model import (
    PunktInformationType,
    PunktInformationTypeAnvendelse,
)


def test_indset_punktinformationtype(firedb):
    infotype = PunktInformationType(
        name="ATTR:TEST",
        anvendelse=PunktInformationTypeAnvendelse.FLAG,
        beskrivelse="Bare en test",
    )
    firedb.indset_punktinformationtype(infotype)
    typ = firedb.hent_punktinformationtype("ATTR:TEST")

    assert typ.beskrivelse == infotype.beskrivelse


def test_hent_punktformationtype_by_id(firedb):
    infotype = PunktInformationType(
        name="NET:TEST",
        anvendelse=PunktInformationTypeAnvendelse.FLAG,
        beskrivelse="Net med testpunkter",
    )
    firedb.indset_punktinformationtype(infotype)
    typ = firedb.hent_punktinformationtype("NET:TEST")
    assert typ is not None
    assert typ.name == "NET:TEST"


def test_hent_alle_punktinformationtyper(firedb):
    # Denne test antager at tests ovenfor er kørt først
    all = list(firedb.hent_punktinformationtyper())
    assert len(all) > 0


def test_hent_punktinformationtyper_for_namespace(firedb):
    # Denne test antager at tests ovenfor er kørt først
    all = list(firedb.hent_punktinformationtyper())
    filter = list(firedb.hent_punktinformationtyper(namespace="ATTR"))
    assert len(all) > len(filter)
