import pytest

import fire
from fire.api.model import (
    PunktInformation,
    PunktInformationType,
    PunktInformationTypeAnvendelse,
    Ident,
    FikspunktsType,
    Punkt,
    GeometriObjekt,
    Point,
)


def lav_ident(variant, ident):
    pit = PunktInformationType(
        name=variant,
        anvendelse=PunktInformationTypeAnvendelse.TEKST,
        beskrivelse="Bare en test",
    )
    return Ident(PunktInformation(infotype=pit, tekst=ident))


def test_ident_sortering():
    gi = lav_ident("IDENT:GI", "G.M.902")
    gnss = lav_ident("IDENT:GNSS", "SKEJ")
    gnss2 = lav_ident("IDENT:GNSS", "AAAA")
    landsnr = lav_ident("IDENT:landsnr", "102-08-00802")
    jessen = lav_ident("IDENT:jessen", "81412")
    station = lav_ident("IDENT:station", "1321")
    ekstern = lav_ident("IDENT:ekstern", "88-01-2342")
    diverse = lav_ident("IDENT:diverse", "flaf")
    refgeoid = lav_ident("IDENT:refgeo_id", "12345")

    assert [gi, gnss, jessen] == sorted([jessen, gnss, gi])
    assert [gi, gnss, landsnr, jessen, station, ekstern, diverse, refgeoid] == sorted(
        [refgeoid, ekstern, station, landsnr, gi, diverse, jessen, gnss]
    )

    assert gnss > gnss2


def test_lighed():
    gi = lav_ident("IDENT:GI", "G.M.902")

    assert gi == "G.M.902"
    assert gi == gi
    assert str(gi) == "G.M.902"


def test_ident_type():
    gi = lav_ident("IDENT:GI", "G.M.902")

    assert gi.variant == "IDENT:GI"


def test_instantiering_af_ikke_ident():
    with pytest.raises(ValueError):
        lav_ident("ATTR:TEST", "I hvert fald ikke en ident")


def test_integration_tilknyt_landsnumre(firedb):
    """
    Integrationstest af FireDb.tilknyt_landsnumre.
    """
    punkt_ider = [
        "b3d47ca0-cfaa-484c-84d6-c864bbed133a",
        "182a6be2-b048-48f9-8af7-093cc891f43d",
        "e2122480-ee8c-48c1-b89c-eb7fad18490b",
    ]
    fikspunktstyper = [
        FikspunktsType.HØJDE,
        FikspunktsType.HØJDE,
        FikspunktsType.HØJDE,
    ]

    # Hvis test-suiten køres flere gange uden at databasen nulstilles kan vi
    # ikke regne med stabilt landsnummer output i denne test.  Vi sjusser os frem
    # til det rigtige svar på baggrund af databasens nuværende indhold
    n = (
        firedb.session.query(PunktInformation)
        .filter(PunktInformation.tekst.startswith("K-63-0900"))
        .count()
    )

    punkter = firedb.hent_punkt_liste(punkt_ider)
    landsnumre = firedb.tilknyt_landsnumre(punkter, fikspunktstyper)

    for i, landsnummer in enumerate(landsnumre, n + 1):
        assert landsnummer.tekst == f"K-63-09{i:0>3}"


def test_unit_tilknyt_landsnumre(dummydb, mocker):
    """
    Test at løbenumre tildeles korrekt med afsæt i allerede tildelte
    løbenumre.
    """
    punkt_ider = [fire.uuid() for _ in range(3)]

    se = (("K-63", pid) for pid in punkt_ider)
    mocker.patch(
        "fire.api.FireDb.hent_punktinformationtype",
        return_value=PunktInformationType(name="IDENT:landsnr"),
    )
    mocker.patch("fire.api.FireDb._opmålingsdistrikt_fra_punktid", return_value=se)
    mocker.patch(
        "fire.api.FireDb._løbenumre_i_distrikt",
        return_value=["09001", "09002", "09003"],
    )

    punkter = [
        Punkt(
            id=pktid, geometriobjekter=[GeometriObjekt(geometri=Point((56.15, 10.20)))]
        )
        for pktid in punkt_ider
    ]

    fikspunktstyper = [
        FikspunktsType.HØJDE,
        FikspunktsType.HØJDE,
        FikspunktsType.HØJDE,
    ]

    print(fikspunktstyper)
    print(punkter)
    landsnumre = dummydb.tilknyt_landsnumre(punkter, fikspunktstyper)

    assert len(landsnumre) == 3

    for i, landsnummer in enumerate(landsnumre, 4):
        assert landsnummer.tekst == f"K-63-0900{i}"


def test_unit_tilknyt_landsnumre_gi(dummydb, mocker):
    """
    Test løbenummerudvælgelse for GI-punkter hvor der er løbenumrene
    befinder sig i to intervaller. Specifikt testes om overgangen fra
    det første interval til det andet forløber som det skal.
    """

    punkt_ider = [fire.uuid() for _ in range(4)]

    se = (("K-63", pid) for pid in punkt_ider)
    mocker.patch(
        "fire.api.FireDb.hent_punktinformationtype",
        return_value=PunktInformationType(name="IDENT:landsnr"),
    )
    mocker.patch("fire.api.FireDb._opmålingsdistrikt_fra_punktid", return_value=se)
    mocker.patch(
        "fire.api.FireDb._løbenumre_i_distrikt",
        return_value=[str(i).zfill(5) for i in range(1, 9)],
    )

    punkter = [
        Punkt(
            id=pktid, geometriobjekter=[GeometriObjekt(geometri=Point((56.15, 10.20)))]
        )
        for pktid in punkt_ider
    ]

    fikspunktstyper = [
        FikspunktsType.GI,
        FikspunktsType.GI,
        FikspunktsType.GI,
        FikspunktsType.GI,
    ]

    print(fikspunktstyper)
    print(punkter)
    landsnumre = dummydb.tilknyt_landsnumre(punkter, fikspunktstyper)

    assert len(landsnumre) == 4

    forventede_landsnumre = [
        "K-63-00009",
        "K-63-00010",
        "K-63-00801",
        "K-63-00802",
    ]

    for landsnr, forventet in zip(landsnumre, forventede_landsnumre):
        assert landsnr.tekst == forventet


def test_unit_tilknyt_landsnumre_flere_typer(dummydb, mocker):
    """
    Test løbenummerudvælgelse for flere typer fikspunktpunkter i samme kald.
    """

    punkt_ider = [fire.uuid() for _ in range(5)]

    se = (("K-63", pid) for pid in punkt_ider)
    mocker.patch(
        "fire.api.FireDb.hent_punktinformationtype",
        return_value=PunktInformationType(name="IDENT:landsnr"),
    )
    mocker.patch("fire.api.FireDb._opmålingsdistrikt_fra_punktid", return_value=se)
    mocker.patch(
        "fire.api.FireDb._løbenumre_i_distrikt",
        return_value=[],
    )

    punkter = [
        Punkt(
            id=pktid, geometriobjekter=[GeometriObjekt(geometri=Point((56.15, 10.20)))]
        )
        for pktid in punkt_ider
    ]

    fikspunktstyper = [
        FikspunktsType.GI,
        FikspunktsType.MV,
        FikspunktsType.HØJDE,
        FikspunktsType.JESSEN,
        FikspunktsType.HJÆLPEPUNKT,
    ]

    print(fikspunktstyper)
    print(punkter)
    landsnumre = dummydb.tilknyt_landsnumre(punkter, fikspunktstyper)

    assert len(landsnumre) == 5

    forventede_landsnumre = [
        "K-63-00001",
        "K-63-00011",
        "K-63-09001",
        "K-63-81001",
        "K-63-90001",
    ]

    for landsnr, forventet in zip(landsnumre, forventede_landsnumre):
        assert landsnr.tekst == forventet


def test_unit_tilknyt_landsnumre_har_landsnr(dummydb, mocker):
    """
    Test at punkter der allerede har et landsnummer frasorteres.
    """

    pktid = fire.uuid()

    pit_landsnr = PunktInformationType(name="IDENT:landsnr")
    mocker.patch("fire.api.FireDb.hent_punktinformationtype", return_value=pit_landsnr)
    mocker.patch(
        "fire.api.FireDb._opmålingsdistrikt_fra_punktid", return_value=[("K-63", pktid)]
    )
    mocker.patch(
        "fire.api.FireDb._løbenumre_i_distrikt",
        return_value=[str(i).zfill(5) for i in range(1, 9)],
    )

    punkter = [
        Punkt(
            id=pktid,
            geometriobjekter=[GeometriObjekt(geometri=Point((56.15, 10.20)))],
            punktinformationer=[
                PunktInformation(infotype=pit_landsnr, tekst="K-63-00001")
            ],
        )
    ]
    fikspunktstyper = [FikspunktsType.GI]
    landsnumre = dummydb.tilknyt_landsnumre(punkter, fikspunktstyper)

    assert len(landsnumre) == 0


def test_unit_tilknyt_landsnumre_fejl_ved_manglende_geometri(dummydb, mocker):
    """
    Test at der er smides en exception når et Punkt mangler en geometri.
    """
    pktid = fire.uuid()

    pit_landsnr = PunktInformationType(name="IDENT:landsnr")
    mocker.patch("fire.api.FireDb.hent_punktinformationtype", return_value=pit_landsnr)

    punkter = [Punkt(id=pktid)]
    fikspunktstyper = [FikspunktsType.GI]

    with pytest.raises(AttributeError):
        dummydb.tilknyt_landsnumre(punkter, fikspunktstyper)


def test_unit_tilknyt_landsnumre_fejl_punkttyper_exceptions(dummydb, mocker):
    """
    Test at der er smides en exception ved ugyldige FikspunktsTyper.
    """
    pktid = fire.uuid()

    pit_landsnr = PunktInformationType(name="IDENT:landsnr")
    mocker.patch("fire.api.FireDb.hent_punktinformationtype", return_value=pit_landsnr)
    mocker.patch(
        "fire.api.FireDb._opmålingsdistrikt_fra_punktid", return_value=[("K-63", pktid)]
    )
    mocker.patch(
        "fire.api.FireDb._løbenumre_i_distrikt",
        return_value=[str(i).zfill(5) for i in range(1, 9)],
    )

    punkter = [
        Punkt(
            id=pktid, geometriobjekter=[GeometriObjekt(geometri=Point((56.15, 10.20)))]
        )
    ]
    fikspunktstyper = [FikspunktsType.VANDSTANDSBRÆT]

    with pytest.raises(NotImplementedError):
        dummydb.tilknyt_landsnumre(punkter, fikspunktstyper)

    fikspunktstyper = ["IKKE_EN_FIKSPUNKSTYPE"]
    with pytest.raises(ValueError):
        dummydb.tilknyt_landsnumre(punkter, fikspunktstyper)


def test_unit_tilknyt_gi_numre(firedb, punktfabrik):
    """
    Test at tilknyt_gi_numre fungerer som forventet.
    """
    punkter = [punktfabrik() for _ in range(3)]
    punktinfo = firedb.tilknyt_gi_numre(punkter)

    assert punktinfo[0].infotype == firedb.hent_punktinformationtype("IDENT:GI")

    assert punktinfo[0].tekst == "G.I.2223"
    assert punktinfo[1].tekst == "G.I.2224"
    assert punktinfo[2].tekst == "G.I.2225"

    firedb.session.rollback()
