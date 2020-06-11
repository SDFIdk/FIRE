import pytest

from fire.api.model import (
    PunktInformation,
    PunktInformationType,
    PunktInformationTypeAnvendelse,
    Ident,
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
