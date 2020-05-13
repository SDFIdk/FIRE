from fire.api.model import (
    PunktInformation,
    Sagsevent,
)


def test_indset_punktinformation(firedb, sag, punkt, punktinformationtype):
    pi = PunktInformation(infotype=punktinformationtype, punkt=punkt)
    firedb.indset_punktinformation(Sagsevent(sag=sag), pi)
