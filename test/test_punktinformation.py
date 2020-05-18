from fire.api import FireDb
from fire.api.model import (
    Punkt,
    PunktInformation,
    PunktInformationType,
    Sagsevent,
    EventType,
)


def test_indset_punktinformation(firedb, sag, punkt, punktinformationtype):
    pi = PunktInformation(infotype=punktinformationtype, punkt=punkt)
    firedb.indset_punktinformation(Sagsevent(sag=sag), pi)


def test_opdatering_punktinformation(firedb, sag, punkt):
    pit = firedb.hent_punktinformationtype("IDENT:landsnr")

    se1 = Sagsevent(sag=sag)
    pi1 = PunktInformation(infotype=pit, punkt=punkt, tekst="K-12-1231")
    firedb.indset_punktinformation(se1, pi1)

    se2 = Sagsevent(sag=sag)
    pi2 = PunktInformation(infotype=pit, punkt=punkt, tekst="K-22-2231")
    firedb.indset_punktinformation(se2, pi2)

    infotyper = (
        firedb.session.query(PunktInformation)
        .filter(
            PunktInformation.infotypeid == pit.infotypeid,
            PunktInformation.punktid == punkt.id,
        )
        .all()
    )

    assert len(infotyper) == 2
    assert infotyper[0].registreringtil == infotyper[1].registreringfra
    assert infotyper[0].sagseventtilid == infotyper[1].sagseventfraid


def test_luk_punktinfo(
    firedb: FireDb,
    punktinformationtype: PunktInformationType,
    punkt: Punkt,
    sagsevent: Sagsevent,
):
    punktinfo = PunktInformation(
        infotype=punktinformationtype, punkt=punkt, sagsevent=sagsevent
    )
    firedb.session.add(punktinfo)
    firedb.session.commit()
    assert punktinfo.registreringtil is None

    firedb.luk_punktinfo(punktinfo, sagsevent)
    assert punktinfo.registreringtil is not None
    assert punktinfo.sagsevent.eventtype == EventType.PUNKTINFO_FJERNET
