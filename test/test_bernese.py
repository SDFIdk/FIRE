"""
Kør Bernese fillæser med testdata
"""
import math
import warnings
from pathlib import Path

import pytest

from fire.io.bernese import BerneseSolution, Kovarians


ADDNEQ1273 = Path("test/data/ADDNEQ2_1273")
CRD1273 = Path("test/data/COMB1273.CRD")

ADDNEQ1886 = Path("test/data/ADDNEQ2_1886")
CRD1886 = Path("test/data/COMB1886.CRD")
COV1886 = Path("test/data/COMB1886.COV")

ADDNEQ2096 = Path("test/data/ADDNEQ2_2096")
CRD2096 = Path("test/data/COMB2096.CRD")
COV2096 = Path("test/data/COMB2096.COV")


def test_bernesesolution():
    """
    Indlæs og test output fra tre konkrete sæt med forskellige værdier og sektionsformater
    """
    # Datasæt 1 - første sæt, uden eksisterende COV-fil eller spredning

    reader1 = BerneseSolution(
        addneq_fil=ADDNEQ1273,  # denne fil har ingen spredningssektion
        crd_fil=CRD1273,
    )  # undlad at angive COV-fil
    assert reader1.gnss_uge == 1273
    assert reader1.epoke.year == 2004
    assert reader1.epoke.month == 6
    assert reader1.epoke.day == 2
    assert reader1.epoke.second == 0
    assert reader1.epoke.microsecond == 0
    assert reader1.datum == "IGb08"
    assert reader1["MAR6"].dagsresidualer is None
    assert reader1["HERT"].kovarians is None
    assert reader1["HHLM"].flag == "A"
    assert reader1["BOR1"].obsstart.year == 2004
    assert reader1["BOR1"].obsstart.month == 6
    assert reader1["BOR1"].obsstart.day == 1
    assert reader1["BOR1"].obsstart.hour == 0
    assert reader1["BOR1"].obsstart.minute == 0
    assert reader1["BOR1"].obsstart.second == 0
    assert reader1["BOR1"].obsslut.year == 2004
    assert reader1["BOR1"].obsslut.month == 6
    assert reader1["BOR1"].obsslut.day == 3
    assert reader1["BOR1"].obsslut.hour == 23
    assert reader1["BOR1"].obsslut.minute == 59
    assert reader1["BOR1"].obsslut.second == 30
    assert str(reader1["BOR1"].obslængde) == "2 days, 23:59:30"
    assert math.isclose(a=reader1["BUDP"].koordinat.x, b=3513638.26170)
    assert math.isclose(a=reader1["BUDP"].koordinat.y, b=778956.38829)
    assert math.isclose(a=reader1["BUDP"].koordinat.z, b=5248216.43002)

    # Datasæt 2 - tidligste sæt med alle tre filer

    reader2 = BerneseSolution(
        addneq_fil=ADDNEQ1886,
        crd_fil=CRD1886,
        cov_fil=COV1886,
    )
    assert reader2.gnss_uge == 1886
    assert reader2.epoke.year == 2016
    assert reader2.epoke.month == 3
    assert reader2.epoke.day == 4
    assert reader2.epoke.second == 0
    assert reader2.epoke.microsecond == 0
    assert reader2.datum == "IGb08"
    assert math.isclose(a=float(reader2["MAR6"].dagsresidualer.sn), b=0.12)
    assert math.isclose(a=float(reader2["MAR6"].dagsresidualer.se), b=0.11)
    assert math.isclose(a=float(reader2["MAR6"].dagsresidualer.su), b=0.36)
    assert math.isclose(
        a=float(reader2["MAR6"].dagsresidualer.n_residualer[0]), b=-0.12
    )

    w = 0.0009**2
    assert reader2["ESBC"].kovarians == Kovarians(
        xx=0.1442016297 * w,
        yy=0.02864337257 * w,
        zz=0.2674335932 * w,
        yx=0.01928893236 * w,
        zx=0.1507957187 * w,
        zy=0.02412103176 * w,
    )
    assert reader2["FYHA"].flag == "A"
    assert math.isclose(a=reader2["BUDP"].koordinat.x, b=3513638.07857)
    assert math.isclose(a=reader2["BUDP"].koordinat.y, b=778956.56481)
    assert math.isclose(a=reader2["BUDP"].koordinat.z, b=5248216.53648)

    # Datasæt 3 - nyeste sæt med alle tre filer

    reader3 = BerneseSolution(
        addneq_fil=ADDNEQ2096,
        crd_fil=CRD2096,
        cov_fil=COV2096,
    )

    assert reader3.gnss_uge == 2096
    assert reader3.epoke.year == 2020
    assert reader3.epoke.month == 3
    assert reader3.epoke.day == 11
    assert reader3.epoke.second == 0
    assert reader3.epoke.microsecond == 0
    assert reader3.datum == "IGS14"
    assert reader3["RIKO"].obsstart.year == 2020
    assert reader3["RIKO"].obsstart.month == 3
    assert reader3["RIKO"].obsstart.day == 10
    assert reader3["RIKO"].obsstart.hour == 0
    assert reader3["RIKO"].obsstart.minute == 0
    assert reader3["RIKO"].obsstart.second == 0
    assert reader3["RIKO"].obsslut.year == 2020
    assert reader3["RIKO"].obsslut.month == 3
    assert reader3["RIKO"].obsslut.day == 12
    assert reader3["RIKO"].obsslut.hour == 23
    assert reader3["RIKO"].obsslut.minute == 59
    assert reader3["RIKO"].obsslut.second == 30
    assert math.isclose(a=float(reader3["MAR6"].dagsresidualer.sn), b=0.91)
    assert math.isclose(a=float(reader3["MAR6"].dagsresidualer.se), b=1.02)
    assert math.isclose(a=float(reader3["MAR6"].dagsresidualer.su), b=2.98)
    assert math.isclose(
        a=float(reader3["MAR6"].dagsresidualer.n_residualer[0]), b=-0.07
    )
    assert math.isclose(a=float(reader3["MAR6"].dagsresidualer.n_residualer[1]), b=0.95)
    assert math.isclose(
        a=float(reader3["MAR6"].dagsresidualer.n_residualer[2]), b=-0.87
    )

    w = 0.0010**2
    assert reader3["ONSA"].kovarians == Kovarians(
        xx=0.06792032947 * w,
        yy=0.01283152234 * w,
        zz=0.1508975287 * w,
        yx=0.01151628674 * w,
        zx=0.07605137984 * w,
        zy=0.01515196666 * w,
    )
    assert reader3["FYHA"].flag == "A"
    assert math.isclose(a=reader3["BUDP"].koordinat.x, b=3513638.01440)
    assert math.isclose(a=reader3["BUDP"].koordinat.y, b=778956.62349)
    assert math.isclose(a=reader3["BUDP"].koordinat.z, b=5248216.57412)


def test_bernese_koordinat():
    """Test at koordinat fra ADDNEQ-fil læses korrekt."""
    BUDP = BerneseSolution(ADDNEQ1886, CRD1886)["BUDP"]

    assert BUDP.koordinat.x == 3513638.07857
    assert BUDP.koordinat.y == 778956.56481
    assert BUDP.koordinat.z == 5248216.53648
    assert BUDP.koordinat.sx == 0.00034
    assert BUDP.koordinat.sy == 0.00015
    assert BUDP.koordinat.sz == 0.00047


def test_bernese_koordinat_kovarians():
    """Test at den samlede løsnings kovariansmatrix læses korrekt."""
    BUDP = BerneseSolution(ADDNEQ2096, CRD2096, COV2096)["BUDP"]

    skalering = 0.001**2
    assert BUDP.kovarians.xx == 0.9145031116e-01 * skalering
    assert BUDP.kovarians.yx == 0.1754111808e-01 * skalering
    assert BUDP.kovarians.zx == 0.9706757931e-01 * skalering
    assert BUDP.kovarians.yy == 0.1860172410e-01 * skalering
    assert BUDP.kovarians.zy == 0.2230707662e-01 * skalering
    assert BUDP.kovarians.zz == 0.1740501496e00 * skalering

    # Kontroller at spredning bestemt fra kovariansmatrix er ens med spredning
    # aflæst i ADDNEQ-filen. Vi har kun 5 decimaler til rådighed ved læsning af
    # koordinatspredningerne derfor sættes abs_tol=1e-5
    assert math.isclose(math.sqrt(BUDP.kovarians.xx), BUDP.koordinat.sx, abs_tol=1e-5)
    assert math.isclose(math.sqrt(BUDP.kovarians.yy), BUDP.koordinat.sy, abs_tol=1e-5)
    assert math.isclose(math.sqrt(BUDP.kovarians.zz), BUDP.koordinat.sz, abs_tol=1e-5)


def test_bernesesolution_paths():
    """
    Kontroller at både str og Path virker som fil-input, samt fejlhåndtering virker som
    """

    # Hvis ingen exceptions fanges her må vi forvente at filerne læses korrekt
    BerneseSolution(str(ADDNEQ1886), str(CRD1886), str(COV1886))
    BerneseSolution(ADDNEQ1886, CRD1886, COV1886)

    with pytest.raises(TypeError):
        BerneseSolution(234, 2342, 234)

    with pytest.raises(TypeError):
        BerneseSolution(ADDNEQ1886, 2342, 234)

    with pytest.raises(TypeError):
        BerneseSolution(ADDNEQ1886, CRD1886, 234)

    with pytest.raises(FileNotFoundError):
        BerneseSolution("fil_findes_ikke", CRD1886)

    with pytest.raises(FileNotFoundError):
        BerneseSolution(ADDNEQ1886, "fil_findes_ikke")

    with pytest.raises(FileNotFoundError):
        BerneseSolution(ADDNEQ1886, CRD1886, "fil_findes_ikke")


def test_bernese_residualer():
    """
    Test at dagsresidualer omregnes til kovariansmatrix korrekt.
    """
    BUDP = BerneseSolution(ADDNEQ2096, CRD2096, COV2096)["BUDP"]

    vn = BUDP.dagsresidualer.kovarians_neu[0][0]
    ve = BUDP.dagsresidualer.kovarians_neu[1][1]
    vu = BUDP.dagsresidualer.kovarians_neu[2][2]

    # spredninger er kun givet med to decimalers nøjagtighed i ADDNEQ-filen
    # derfor testes med en relativt dårlig nøjagtighed. Det burde være
    # tilstrækkeligt til at verificere at kovariansmatrixen er opstillet korrekt.
    assert math.isclose(math.sqrt(vn), BUDP.dagsresidualer.sn, abs_tol=1e-2)
    assert math.isclose(math.sqrt(ve), BUDP.dagsresidualer.se, abs_tol=1e-2)
    assert math.isclose(math.sqrt(vu), BUDP.dagsresidualer.su, abs_tol=1e-2)


def test_kovariansmatrix_nok_frihedsgrader():
    """
    Test at residualkovariansmatrix håndteres pænt i tilfælde hvor der kun er
    residualer fra en dagsløsning til rådighed.

    Her tester vi med data fra MAR6-stationen hvor der er regnet en enkelt
    dagsløsning.
    """
    MAR6 = BerneseSolution(ADDNEQ1886, CRD1886, COV1886)["MAR6"]

    # numpy.cov giver en RuntimeWarning hvis der ikke er nok data
    # til at lave en kovariansmatrix. Vi forsøger at undgå det men
    # skulle det skal vil vi gerne gøres opmærksom på det.
    with warnings.catch_warnings():
        # bekræft at der ikke genereres en kovariansmatrix når der ikke
        # er tilstrækkeligt data
        assert MAR6.dagsresidualer.kovarians_neu is None


def test_bernesesolution_sortering():
    solutions = sorted(
        [
            BerneseSolution(ADDNEQ1886, CRD1886),
            BerneseSolution(ADDNEQ2096, CRD2096),
            BerneseSolution(ADDNEQ1273, CRD1273),
        ]
    )

    assert solutions[0].gnss_uge == 1273
    assert solutions[1].gnss_uge == 1886
    assert solutions[2].gnss_uge == 2096
