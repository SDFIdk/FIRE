from fireapi.model import *


def test_indset_punktinformation(firedb, sag, punkt, punktinformationtype):
    pi = PunktInformation(infotype=punktinformationtype.infotype, punkt=punkt)
    firedb.indset_punktinformation(Sagsevent(sag=sag), pi)
