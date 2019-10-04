from fireapi.model import *


def test_hent_punktformationtype_by_id(firedb):
    typ = firedb.hent_punktinformationtype("AFM:horisontal")
    assert typ is not None
    assert typ.name == "AFM:horisontal"


def test_hent_alle_punktinformationtyper(firedb):
    all = list(firedb.hent_punktinformationtyper())
    assert len(all) > 0


def test_hent_punktinformationtyper_for_namespace(firedb):
    all = list(firedb.hent_punktinformationtyper())
    filter = list(firedb.hent_punktinformationtyper(namespace="AFM"))
    assert len(all) > len(filter)


def test_indset_punktinformationtype(firedb):
    infotype = PunktInformationType(
        name="ATTR:TEST",
        anvendelse=PunktInformationTypeAnvendelse.FLAG,
        beskrivelse="Bare en test",
    )
    firedb.indset_punktinformationtype(infotype)
    typ = firedb.hent_punktinformationtype("ATTR:TEST")

    assert typ.beskrivelse == infotype.beskrivelse
