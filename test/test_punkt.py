from typing import List
from itertools import chain

from sqlalchemy.orm.exc import NoResultFound
import pytest

from fire.api import FireDb
from fire.api.model import (
    Sagsevent,
    SagseventInfo,
    Punkt,
    Observation,
    Koordinat,
    PunktInformation,
    PunktInformationType,
    GeometriObjekt,
    Point,
    Sag,
    EventType,
)


def test_punkt(firedb: FireDb, punkt: Punkt):
    firedb.session.commit()


def test_punkt_geometri():
    p = Punkt()
    go = GeometriObjekt()
    go.geometri = Point([1, 2])
    p.geometriobjekter.append(go)
    assert p.geometri.koordinater[0] == 1
    assert p.geometri.koordinater[1] == 2


def test_indset_punkt(firedb: FireDb, sag: Sag):
    p = Punkt()
    go = GeometriObjekt()
    go.geometri = Point([1, 1])
    p.geometriobjekter.append(go)

    firedb.indset_sagsevent(
        Sagsevent(
            sag=sag,
            sagseventinfos=[SagseventInfo(beskrivelse="Testindsættelse af et punkt")],
            eventtype=EventType.PUNKT_OPRETTET,
            punkter=[p],
        )
    )


def test_indset_flere_punkter(firedb: FireDb, sag: Sag):
    p = Punkt()
    go = GeometriObjekt()
    go.geometri = Point([1, 1])
    p.geometriobjekter.append(go)

    q = Punkt()
    go = GeometriObjekt()
    go.geometri = Point([2, 2])
    q.geometriobjekter.append(go)

    firedb.indset_sagsevent(
        Sagsevent(
            sag=sag,
            eventtype=EventType.PUNKT_OPRETTET,
            sagseventinfos=[
                SagseventInfo(beskrivelse="Testindsættelse af flere punkter")
            ],
            punkter=[p, q],
        )
    )


def test_hent_punkt(firedb: FireDb, punkt: Punkt):
    firedb.session.commit()  # sørg for at punkt indsættes i databasen
    punktid = punkt.id
    print(punktid)
    print(punkt)
    p = firedb.hent_punkt(punktid)
    assert isinstance(p, Punkt)
    s = p.sagsevent
    assert isinstance(s, Sagsevent)

def test_hent_punkter(firedb: FireDb):
    """
    Test at alle punkter med ækvivalente GNSS ID'er fremsøges korrekt.

    Historisk er GNSS ID navngivet med 4 tegn. Det har gennem tid skabt konflikt
    med punkter i DK og GL, hvorfor de grønlandske punkter har fået præfixet "GL  ".
    Sidenhen er 9-tegns GNSS ID'er kommet til, netop for at undgå denne
    problemstilling. FIRE skal kunne fremsøge dem alle vha af 4-tegns betegnelsen,
    som normalt bruges i daglig tale. Præfix og fuldt 9-tegns ID kan hjælpe med
    at fjerne tvivl i tilfælde flere punkter dukker op i en søgning.
    """
    forventede_punkter = ["RDO1", "RDO100GRL", "GL  RDO1"]
    punkter = firedb.hent_punkter("RDO1")

    assert len(punkter) == 3
    for punkt in punkter:
        assert punkt.gnss_navn in forventede_punkter



def test_hent_punkt(firedb: FireDb):
    """
    Test at `hent_punkt()` returnerer det eksakte match i tilfælde af der
    findes ens identer, hvor et eller flere har foranstillet landekode.
    Eksempelvis "SAND" og "FO  SAND". Her tester vi med "RDO1" og "GL  RDO1"
    der er opfundet til lejligheden.
    Ligeledes testes om der skelnes korrekt mellem "RDO1" og "RDO100GRL".
    """
    punkt = firedb.hent_punkt("RDO1")
    assert punkt.gnss_navn == "RDO1"

    punkt = firedb.hent_punkt("GL  RDO1")
    assert punkt.gnss_navn == "GL  RDO1"

    punkt = firedb.hent_punkt("RDO100GRL")
    assert punkt.gnss_navn == "RDO100GRL"


def test_hent_alle_punkter(firedb: FireDb):
    p = firedb.hent_alle_punkter()
    assert isinstance(p, list)


def test_luk_punkt(
    firedb: FireDb,
    punkt: Punkt,
    sagsevent: Sagsevent,
    observationer: List[Observation],
    koordinat: Koordinat,
    punktinformationtype: PunktInformationType,
):
    # byg et punkt der har tilknyttet geometri, koordinat,
    # punktinfo og observationer
    geometri = GeometriObjekt(
        punkt=punkt, geometri=Point([10, 55]), sagsevent=sagsevent
    )
    firedb.session.add(geometri)
    observationer[0].opstillingspunkt = punkt
    observationer[1].sigtepunkt = punkt
    koordinat.punkt = punkt
    punkt.punktinformationer = [
        PunktInformation(infotype=punktinformationtype, sagsevent=sagsevent)
    ]
    firedb.session.commit()

    firedb.luk_punkt(punkt, sagsevent)
    assert punkt.registreringtil is not None
    assert punkt.sagsevent.eventtype == EventType.PUNKT_NEDLAGT
    assert punkt.sagseventtilid == sagsevent.id
    assert geometri.registreringtil is not None
    assert geometri.sagsevent.eventtype == EventType.PUNKT_NEDLAGT

    for koordinat in punkt.koordinater:
        assert koordinat.registreringtil is not None
        assert koordinat.sagsevent.eventtype == EventType.PUNKT_NEDLAGT
        assert koordinat.sagseventtilid == sagsevent.id

    for punktinfo in punkt.punktinformationer:
        assert punktinfo.registreringtil is not None
        assert punktinfo.sagsevent.eventtype == EventType.PUNKT_NEDLAGT
        assert punktinfo.sagseventtilid == sagsevent.id

    for observation in chain(punkt.observationer_fra, punkt.observationer_til):
        assert observation.registreringtil is not None
        assert observation.sagsevent.eventtype == EventType.PUNKT_NEDLAGT
        assert observation.sagseventtilid == sagsevent.id

    with pytest.raises(TypeError):
        firedb.luk_punkt(999)


def test_ident(firedb: FireDb, punkt: Punkt):
    """
    Test at Punkt.ident returnerer det forventede ident.

    I testdatasættet forekommer to identer til GNSS stationen i Skejby:
    IDENT:GNSS == SKEJ og IDENT:landsnr == 102-08-00802. Førstnænvte
    skal returneres.
    """

    assert punkt.ident == punkt.id

    punkt = firedb.hent_punkt("8e5e57f8-d3c4-45f2-a2a9-492f52d7df1c")

    assert punkt.ident == "SKEJ"


def test_identer(firedb: FireDb):
    punkt = firedb.hent_punkt("8e5e57f8-d3c4-45f2-a2a9-492f52d7df1c")

    assert "SKEJ" in punkt.identer
    assert "102-08-00802" in punkt.identer
    assert len(punkt.identer) == 3  # kort uuid 8e5e57f8 er også en ident


def test_punkt_cache(firedb: FireDb):
    punkt = firedb.hent_punkt("8e5e57f8-d3c4-45f2-a2a9-492f52d7df1c")

    assert punkt is firedb.hent_punkt("SKEJ")
    assert punkt is firedb.hent_punkt("102-08-00802")
    assert punkt is firedb.hent_punkt("8e5e57f8-d3c4-45f2-a2a9-492f52d7df1c")


def test_hent_punkt_liste(firedb: FireDb):
    identer = ["RDIO", "RDO1", "SKEJ"]
    punkter = firedb.hent_punkt_liste(identer)

    for ident, punkt in zip(identer, punkter):
        assert ident == punkt.ident

    with pytest.raises(ValueError):
        firedb.hent_punkt_liste(["SKEJ", "RDIO", "ukendt_ident"], ignorer_ukendte=False)

    punkter = firedb.hent_punkt_liste(
        ["SKEJ", "RDIO", "ukendt_ident"], ignorer_ukendte=True
    )
    assert len(punkter) == 2


def test_hent_punkter_fra_uuid_liste(firedb: FireDb):

    identer = ["RDIO", "RDO1", "G.I.1234"]

    punkter = firedb.hent_punkter_fra_uuid_liste(
        [
            "301b8578-8cc8-48a8-8446-541f31482f86",  # RDIO
            "4b4c5c17-32e8-495d-a598-cdf42e0892de",  # RDO1
            "4871c57b-d325-45fa-a03a-fdcff49273c0",  # G.I.1234
        ]
    )

    for punkt in punkter:
        assert punkt.ident in identer

    # Tjek håndtering af opslag på ikke-eksisterende punkter
    punkter = firedb.hent_punkter_fra_uuid_liste(
        [
            "et-uuid-der-ikke-findes",
            "et-andet-uuid-der-ikke-findes",
        ]
    )

    # Vi forventer en tom liste her
    assert not punkter


def test_soeg_punkter(firedb: FireDb):
    punkter = firedb.soeg_punkter("%rd%")

    for punkt in punkter:
        assert punkt.ident in ("RDIO", "RDO1", "GL  RDO1", "RDO100GRL")

    kun_et_punkt = firedb.soeg_punkter("K-63-%", antal=1)
    assert len(kun_et_punkt) == 1

    with pytest.raises(NoResultFound):
        firedb.soeg_punkter("punkt der ikke findes")
