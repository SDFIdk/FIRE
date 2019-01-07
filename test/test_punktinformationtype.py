from fireapi.model import *


def test_hent_punktformationtype_by_id(firedb):
    typ = firedb.hent_punktinformationtype("AFM:horisontal")
    assert typ is not None
    assert typ.infotype == "AFM:horisontal"


def test_hent_alle_punktinformationtyper(firedb):
    all = list(firedb.hent_punktinformationtyper())
    assert len(all) > 0


def test_hent_punktinformationtyper_for_namespace(firedb):
    all = list(firedb.hent_punktinformationtyper())
    filter = list(firedb.hent_punktinformationtyper(namespace="AFM"))
    assert len(all) > len(filter)
